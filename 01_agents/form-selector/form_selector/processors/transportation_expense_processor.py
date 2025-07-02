"""
교통비 신청서 전용 프로세서

교통비 신청서의 특화된 처리 로직:
- 출발지/목적지 처리
- 교통비 금액 변환 (문자열 → 숫자)
- 출발일 날짜 처리
- 교통 내역 상세 처리
"""

from typing import Dict, Any
from .base_processor import BaseFormProcessor


class TransportationExpenseProcessor(BaseFormProcessor):
    """교통비 신청서 전용 프로세서"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """교통비 전처리"""
        processed_slots = slots.copy()

        # 기본값 설정
        if "title" not in processed_slots or not processed_slots["title"]:
            processed_slots["title"] = "교통비 신청"

        # total_amount 키 보존 - BaseFormProcessor의 None 필터링으로 키가 제거된 경우에도 처리
        if "total_amount" not in processed_slots:
            # None 값으로 인해 키가 제거된 경우
            processed_slots["total_amount"] = 0
        elif processed_slots["total_amount"] == "":  # 빈 문자열 처리
            processed_slots["total_amount"] = 0

        return processed_slots

    def convert_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """교통비 관련 날짜 변환"""
        # 기본 날짜 변환 수행 (departure_date 등이 처리됨)
        converted_slots = super().convert_dates(slots, current_date_iso)

        # 추가적인 교통비 특화 날짜 처리가 필요한 경우 여기에 추가
        # 현재는 기본 처리로 충분함

        return converted_slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        교통비는 아이템 리스트가 없으므로 기본 처리만 수행
        """
        return slots.copy()

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """교통비는 아이템이 없으므로 기본 반환"""
        return slots

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """교통비 특화 필드 변환"""
        converted_slots = super().convert_fields(slots)

        # 금액 필드 처리 - 키가 없는 경우에도 기본값 설정
        converted_slots["total_amount"] = self._convert_amount_to_int(
            converted_slots.get("total_amount")
        )

        return converted_slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """교통비 후처리"""
        processed_slots = slots.copy()

        # 기본값 설정
        if "purpose" not in processed_slots or not processed_slots["purpose"]:
            processed_slots["purpose"] = "업무 관련 교통비"

        # 출발지/목적지 기본값
        if "origin" not in processed_slots or not processed_slots["origin"]:
            processed_slots["origin"] = ""

        if "destination" not in processed_slots or not processed_slots["destination"]:
            processed_slots["destination"] = ""

        return processed_slots

    def _convert_amount_to_int(self, amount_value: Any) -> int:
        """
        금액 값을 정수로 변환

        Args:
            amount_value: 금액 값 (문자열, 숫자, None 등)

        Returns:
            정수 금액 (변환 실패 시 0)
        """
        if amount_value is None:
            return 0

        if isinstance(amount_value, int):
            return amount_value

        if isinstance(amount_value, float):
            return int(amount_value)

        if isinstance(amount_value, str):
            amount_value = amount_value.strip()
            if not amount_value:
                return 0

            try:
                # 숫자가 아닌 문자 제거 (쉼표, 원 등)
                import re

                clean_amount = re.sub(r"[^\d.]", "", amount_value)
                if clean_amount:
                    return int(float(clean_amount))
                else:
                    return 0
            except (ValueError, TypeError):
                return 0

        return 0
