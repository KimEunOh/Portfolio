"""
필드 변환기 클래스

service.py에서 분산되어 있던 필드 매핑 및 값 변환 로직을 통합 관리합니다.
"""

import logging
from typing import Dict, Any


class FieldConverter:
    """필드 매핑 및 값 변환을 전담하는 클래스"""

    # 휴가 종류 텍스트를 HTML <select>의 value로 매핑
    LEAVE_TYPE_TEXT_TO_VALUE_MAP = {
        "연차": "annual",
        "오전 반차": "half_day_morning",
        "오후 반차": "half_day_afternoon",
        "오전 반반차": "quarter_day_morning",
        "오후 반반차": "quarter_day_afternoon",
        "오전반차": "half_day_morning",
        "오후반차": "half_day_afternoon",
        "오전반반차": "quarter_day_morning",
        "오후반반차": "quarter_day_afternoon",
    }

    def convert_leave_type(self, leave_type_text: str) -> str:
        """휴가 종류 텍스트를 HTML <select>의 value로 변환"""
        if leave_type_text in self.LEAVE_TYPE_TEXT_TO_VALUE_MAP:
            converted_value = self.LEAVE_TYPE_TEXT_TO_VALUE_MAP[leave_type_text]
            logging.debug(
                f"Leave type converted: '{leave_type_text}' -> '{converted_value}'"
            )
            return converted_value
        else:
            logging.warning(
                f"Leave type '{leave_type_text}' not found in mapping. Keeping original."
            )
            return leave_type_text

    def convert_overtime_ampm(self, ampm_value: str) -> str:
        """야근 시간 오전/오후 구분 값을 "AM" 또는 "PM"으로 표준화"""
        ampm_upper = ampm_value.upper()

        if "밤" in ampm_value or "오후" in ampm_value or "P" in ampm_upper:
            converted_value = "PM"
        elif "새벽" in ampm_value or "오전" in ampm_value or "A" in ampm_upper:
            converted_value = "AM"
        else:
            converted_value = ampm_value  # 정확히 매칭되지 않으면 원본 유지

        logging.debug(
            f"Overtime AM/PM converted: '{ampm_value}' -> '{converted_value}'"
        )
        return converted_value

    def map_expense_category_to_value(self, category_text: str) -> str:
        """개인 경비 분류 텍스트를 HTML select value로 매핑"""
        if not category_text:
            return ""

        category_lower = category_text.lower()

        # 교통비 관련
        if any(
            keyword in category_lower
            for keyword in [
                "교통",
                "택시",
                "지하철",
                "버스",
                "주차",
                "ktx",
                "항공",
                "유류",
                "톨게이트",
            ]
        ):
            return "traffic"

        # 숙박비 관련
        if any(
            keyword in category_lower
            for keyword in ["숙박", "호텔", "펜션", "게스트하우스", "모텔"]
        ):
            return "accommodation"

        # 식대 관련
        if any(
            keyword in category_lower
            for keyword in [
                "식",
                "음식",
                "커피",
                "음료",
                "카페",
                "식당",
                "회식",
                "점심",
                "저녁",
                "간식",
            ]
        ):
            return "meals"

        # 접대비 관련
        if any(
            keyword in category_lower
            for keyword in [
                "접대",
                "거래처",
                "고객",
                "클라이언트",
                "비즈니스",
                "미팅",
                "상담",
            ]
        ):
            return "entertainment"

        # 교육훈련비 관련
        if any(
            keyword in category_lower
            for keyword in ["교육", "세미나", "연수", "강의", "자격증", "도서"]
        ):
            return "education"

        # 소모품비 관련
        if any(
            keyword in category_lower
            for keyword in ["사무용품", "문구", "소모품", "it용품", "프린터", "복사"]
        ):
            return "supplies"

        # 기타
        return "other"

    def escape_backslashes_for_regex(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """re.sub를 위한 백슬래시 이스케이프 처리"""
        processed_slots = {}

        for key, value in slots.items():
            if isinstance(value, str):
                processed_slots[key] = value.replace("\\", "\\\\")
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, dict):
                        new_dict_item = {}
                        for item_k, item_v in item.items():
                            if isinstance(item_v, str):
                                new_dict_item[item_k] = item_v.replace("\\", "\\\\")
                            else:
                                new_dict_item[item_k] = item_v
                        new_list.append(new_dict_item)
                    elif isinstance(item, str):
                        new_list.append(item.replace("\\", "\\\\"))
                    else:
                        new_list.append(item)
                processed_slots[key] = new_list
            else:
                processed_slots[key] = value

        return processed_slots

    def process_expense_category_mapping(self, expense_items: list) -> list:
        """개인 경비 아이템들의 분류를 HTML select value로 매핑"""
        updated_items = []

        for item in expense_items:
            if isinstance(item, dict):
                processed_item = {**item}

                if "expense_category" in processed_item:
                    category_text = processed_item["expense_category"]
                    category_value = self.map_expense_category_to_value(category_text)
                    processed_item["expense_category"] = category_value
                    logging.debug(
                        f"Expense category mapped: '{category_text}' -> '{category_value}'"
                    )

                updated_items.append(processed_item)
            else:
                updated_items.append(item)

        return updated_items
