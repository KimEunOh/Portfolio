"""
기본 양식 처리기 클래스

템플릿 메서드 패턴을 사용하여 양식 처리의 공통 플로우를 정의합니다.
"""

import logging
import json
import re
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from ..converters import DateConverter, ItemConverter, FieldConverter


class BaseFormProcessor(ABC):
    """양식 처리를 위한 기본 클래스"""

    def __init__(self, form_config: Optional[Any] = None):
        """
        Args:
            form_config: 양식별 설정 정보 (Pydantic 모델 또는 dict)
        """
        if form_config:
            if hasattr(form_config, "dict"):  # Pydantic 모델인지 확인
                self.form_config = (
                    form_config.dict()
                )  # Pydantic v1 호환성을 위해 .dict() 사용
            else:
                self.form_config = form_config
        else:
            self.form_config = {}

        self.date_converter = DateConverter()
        self.item_converter = ItemConverter()
        self.field_converter = FieldConverter()

    def process_slots(
        self,
        slots_dict: Dict[str, Any],
        current_date_iso: str,
        prefer_past: bool = False,
    ) -> Dict[str, Any]:
        """슬롯 처리 템플릿 메서드

        Args:
            slots_dict: LLM으로부터 추출된 원본 슬롯
            current_date_iso: 기준 날짜

        Returns:
            최종 처리된 슬롯 딕셔너리
        """
        logging.info(f"Processing slots with {self.__class__.__name__}")

        # None 값 필터링
        active_slots = {k: v for k, v in slots_dict.items() if v is not None}
        if not active_slots:
            return {}

        # 복사본 생성
        transformed_slots = {**active_slots}

        # 1. 전처리 (양식별 특별 처리)
        transformed_slots = self.preprocess_slots(transformed_slots)

        # 2. 날짜 변환 (최상위 필드)
        transformed_slots = self.date_converter.convert_date_fields(
            transformed_slots, current_date_iso, prefer_past
        )

        # 3. 아이템 내 날짜 변환 (설정 기반)
        if self.form_config and self.form_config.get("items_config"):
            items_config = self.form_config["items_config"]
            list_key = items_config.get("list_key")
            date_key = items_config.get("date_key")

            if (
                list_key in transformed_slots
                and isinstance(transformed_slots[list_key], list)
                and date_key
            ):
                transformed_slots[list_key] = self.date_converter.convert_item_dates(
                    items=transformed_slots[list_key],
                    date_field=date_key,
                    current_date_iso=current_date_iso,
                    prefer_past=prefer_past,
                )

        # 4. 아이템 변환
        transformed_slots = self.convert_items(transformed_slots)

        # 5. 필드 변환
        transformed_slots = self.convert_fields(transformed_slots)

        # 6. 후처리 (양식별 특별 처리)
        transformed_slots = self.postprocess_slots(transformed_slots)

        logging.info(f"Completed slot processing with {self.__class__.__name__}")
        return transformed_slots

    def convert_dates(
        self, slots: Dict[str, Any], current_date_iso: str, prefer_past: bool = False
    ) -> Dict[str, Any]:
        """날짜 변환 공통 로직"""
        # 1. 주요 날짜 필드 변환
        slots = self.date_converter.convert_date_fields(
            slots, current_date_iso, prefer_past
        )

        # 2. 아이템 내 날짜 변환 (설정 기반)
        if self.form_config and self.form_config.get("items_config"):
            items_config = self.form_config["items_config"]
            list_key = items_config.get("list_key")
            date_key = items_config.get("date_key")

            if list_key in slots and isinstance(slots[list_key], list) and date_key:
                slots[list_key] = self.date_converter.convert_item_dates(
                    items=slots[list_key],
                    date_field=date_key,
                    current_date_iso=current_date_iso,
                    prefer_past=prefer_past,
                )

        # 3. 야근 시간 변환 (해당하는 경우)
        if "overtime_time" in slots and isinstance(slots["overtime_time"], str):
            slots["overtime_time"] = self.date_converter.convert_datetime_to_time(
                slots["overtime_time"], current_date_iso
            )

        # 4. 일반 날짜 슬롯 변환
        slots = self.date_converter.convert_general_date_slots(
            slots, current_date_iso, prefer_past=prefer_past
        )

        return slots

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """필드 변환 공통 로직"""
        # 휴가 종류 변환
        if "leave_type" in slots and isinstance(slots["leave_type"], str):
            slots["leave_type"] = self.field_converter.convert_leave_type(
                slots["leave_type"]
            )

        # 야근 AM/PM 변환
        if "overtime_ampm" in slots and isinstance(slots["overtime_ampm"], str):
            slots["overtime_ampm"] = self.field_converter.convert_overtime_ampm(
                slots["overtime_ampm"]
            )

        return slots

    def fill_template(
        self, template: str, slots: Dict[str, Any], current_date_iso: str
    ) -> str:
        """HTML 템플릿에 슬롯 값 채우기"""

        # 백슬래시 이스케이프 처리
        processed_slots = self.field_converter.escape_backslashes_for_regex(slots)

        # JSON 문자열 생성 (아이템 리스트용)
        items_json_str = self.generate_items_json(slots)

        # 플레이스홀더 치환
        def replacer(match):
            key_in_template = match.group(1)

            if key_in_template == "items_json":
                return items_json_str

            if key_in_template == "today":
                return current_date_iso

            value_to_return = processed_slots.get(key_in_template, "")

            if isinstance(value_to_return, str):
                return value_to_return
            else:
                return str(value_to_return)

        filled_template = re.sub(r"{(\w+)}", replacer, template)
        logging.info(f"Template filled successfully by {self.__class__.__name__}")

        return filled_template

    def generate_items_json(self, slots: Dict[str, Any]) -> str:
        """JavaScript용 아이템 JSON 문자열 생성"""
        item_keys = ["items", "expense_items", "card_usage_items"]

        for item_key in item_keys:
            if item_key in slots and isinstance(slots[item_key], list):
                items_list = slots[item_key]
                return json.dumps(items_list, ensure_ascii=False)

        return "null"

    # 추상 메서드들 - 각 양식별 프로세서에서 구현
    @abstractmethod
    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """전처리 단계 - 양식별 특별 처리"""
        pass

    @abstractmethod
    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """아이템 변환 단계 - 양식별 아이템 처리"""
        pass

    @abstractmethod
    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """후처리 단계 - 양식별 최종 처리"""
        pass

    @abstractmethod
    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """아이템 내 날짜 변환 - 양식별 구현"""
        pass

    @abstractmethod
    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """HTML 폼 데이터를 API 페이로드로 변환 - 양식별 구현"""
        pass


class DefaultFormProcessor(BaseFormProcessor):
    """기본 양식 처리기 (특별한 처리가 필요 없는 양식용)"""

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        return slots

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        return slots

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """기본 API 페이로드 변환 (특별한 처리가 필요 없는 양식용)"""
        return form_data
