"""
날짜 변환기 클래스

service.py에서 분산되어 있던 날짜 처리 로직을 통합 관리합니다.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import re
from ..utils import (
    parse_relative_date_to_iso,
    parse_datetime_description_to_iso_local,
    parse_date_range_with_context,
    parse_duration_to_days,
)


def is_duration_string(text: str) -> bool:
    """문자열이 기간(duration) 표현일 가능성이 높은지 확인합니다."""
    if not isinstance(text, str):
        return False
    # 예: "3일", "2 주", "1개월", "5일간", "일주일 동안", "반나절" 등
    duration_pattern = re.compile(
        r"(\d+\s*(일|주|달|개월|년|시간)(간|동안)?)|(하루|이틀|사흘|나흘|닷새|엿새|일주일|한달|반나절)"
    )
    return duration_pattern.search(text) is not None


class DateConverter:
    """날짜 관련 변환을 전담하는 클래스"""

    # 날짜 관련 슬롯 키 이름에 포함될 수 있는 문자열 리스트
    DATE_SLOT_KEY_SUBSTRINGS = ["date", "일자", "기간"]

    def __init__(self):
        # 이 클래스는 특정 폼 설정에 의존하지 않으므로, 생성자에 특별한 설정이 필요 없습니다.
        pass

    def convert_date_fields(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """일반 날짜 필드들을 YYYY-MM-DD 형식으로 변환.
        'start_date'와 'end_date'는 컨텍스트를 유지하며 함께 파싱될 수 있습니다.
        """
        # 동적으로 날짜 필드를 찾기 위한 키워드
        DATE_KEY_SUBSTRINGS = ["date", "day", "ymd"]
        # 날짜 필드에서 제외할 키워드
        EXCLUDE_KEY_SUBSTRINGS = ["duration", "period", "days", "length"]

        # 1. 처리할 모든 날짜 필드를 동적으로 식별
        date_fields_to_process = [
            key
            for key, value in slots.items()
            if isinstance(value, str)
            and any(substr in key.lower() for substr in DATE_KEY_SUBSTRINGS)
            and not any(
                ex_substr in key.lower() for ex_substr in EXCLUDE_KEY_SUBSTRINGS
            )
        ]

        if not date_fields_to_process:
            return slots

        # 2. 'start_date'와 'end_date'가 모두 있는 경우, 우선적으로 함께 처리
        if (
            "start_date" in date_fields_to_process
            and "end_date" in date_fields_to_process
        ):
            end_date_val = slots.get("end_date")

            # end_date가 기간을 나타내는지 먼저 확인
            if (
                isinstance(end_date_val, str)
                and parse_duration_to_days(end_date_val) is not None
            ):
                logging.info(
                    f"end_date '{end_date_val}' is detected as a duration. Skipping combined parsing."
                )
                # start_date만 개별적으로 파싱
                if isinstance(slots["start_date"], str):
                    slots["start_date"] = parse_relative_date_to_iso(
                        slots["start_date"], current_date_iso
                    )
            else:
                # 기간이 아닌 경우에만 동시 파싱 수행
                start_parsed, end_parsed = parse_date_range_with_context(
                    slots["start_date"], slots["end_date"], current_date_iso
                )
                slots["start_date"] = start_parsed
                slots["end_date"] = end_parsed
                logging.info(
                    f"Date range parsed with context: start='{start_parsed}', end='{end_parsed}'"
                )

            # 처리된 start/end date는 개별 처리 목록에서 제외
            date_fields_to_process.remove("start_date")
            if "end_date" in date_fields_to_process:
                date_fields_to_process.remove("end_date")

        # 3. 나머지 날짜 필드들을 개별적으로 파싱
        for field in date_fields_to_process:
            original_value = slots[field]
            if isinstance(original_value, str):
                parsed_value = parse_relative_date_to_iso(
                    original_value, current_date_iso
                )
                if parsed_value != original_value:
                    slots[field] = parsed_value
                    logging.info(
                        f"Parsed date field '{field}': '{original_value}' -> '{parsed_value}'"
                    )

        return slots

    def convert_date_range(
        self, start_date: str, end_date: str, current_date_iso: str
    ) -> Tuple[str, str]:
        """날짜 범위를 컨텍스트 유지하며 변환"""
        return parse_date_range_with_context(start_date, end_date, current_date_iso)

    def convert_item_dates(
        self, items: List[Dict[str, Any]], date_field: str, current_date_iso: str
    ) -> List[Dict[str, Any]]:
        """아이템 리스트 내의 날짜 필드들을 변환"""
        updated_items = []

        for item in items:
            if isinstance(item, dict):
                processed_item = {**item}

                if date_field in processed_item and isinstance(
                    processed_item[date_field], str
                ):
                    original_date_str = processed_item[date_field]
                    parsed_date = parse_relative_date_to_iso(
                        original_date_str, current_date_iso=current_date_iso
                    )

                    if parsed_date:
                        processed_item[date_field] = parsed_date
                        logging.debug(
                            f"Item's '{date_field}' ('{original_date_str}') parsed to '{parsed_date}'"
                        )
                    else:
                        logging.warning(
                            f"Failed to parse {date_field}: {original_date_str}. Keeping original."
                        )

                updated_items.append(processed_item)
            else:
                updated_items.append(item)

        return updated_items

    def convert_datetime_to_time(self, datetime_str: str, current_date_iso: str) -> str:
        """datetime을 time으로 변환 (야근시간 등)"""
        import re

        # 이미 HH:MM 형식인지 확인
        if re.match(r"^\d{1,2}:\d{2}$", datetime_str):
            logging.debug(f"Time '{datetime_str}' is already in HH:MM format")
            return datetime_str

        # 자연어 시간을 파싱 시도
        parsed_datetime = parse_datetime_description_to_iso_local(
            datetime_str, current_date_iso=current_date_iso
        )

        if parsed_datetime and "T" in parsed_datetime:
            time_part = parsed_datetime.split("T")[1]
            logging.info(f"Datetime converted: '{datetime_str}' -> '{time_part}'")
            return time_part
        else:
            logging.warning(
                f"Failed to parse datetime: '{datetime_str}'. Returning empty string."
            )
            return ""

    def convert_general_date_slots(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """일반적인 날짜 슬롯들을 키 이름 기준으로 자동 감지하여 변환"""
        main_date_fields = [
            "start_date",
            "end_date",
            "application_date",
            "work_date",
            "departure_date",
            "request_date",
            "draft_date",
            "statement_date",
            "usage_date",
        ]

        for key, value in list(slots.items()):
            # 이미 처리된 주요 필드는 건너뜀
            if key in main_date_fields:
                continue

            # 날짜 관련 키워드가 포함된 필드만 처리
            if isinstance(value, str) and any(
                substr in key.lower() for substr in self.DATE_SLOT_KEY_SUBSTRINGS
            ):
                original_value = value
                parsed_value = parse_relative_date_to_iso(
                    original_value, current_date_iso=current_date_iso
                )

                if parsed_value and parsed_value != original_value:
                    slots[key] = parsed_value
                    logging.info(
                        f"Parsed date field by substring '{key}': '{original_value}' -> '{parsed_value}'"
                    )
                elif not parsed_value:
                    logging.warning(
                        f"Failed to parse date field by substring '{key}': '{original_value}'. Keeping original."
                    )

        return slots
