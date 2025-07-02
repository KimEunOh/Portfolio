"""
개인 경비 사용내역서 전용 처리기

개인 경비 사용내역서의 특별한 처리 로직을 담당합니다.
- expense_items 처리
- 분류 매핑
- HTML 필드 분해
"""

import logging
from typing import Dict, Any

from .base_processor import BaseFormProcessor


class PersonalExpenseProcessor(BaseFormProcessor):
    """개인 경비 사용내역서 전용 처리기"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)
        logging.info("PersonalExpenseProcessor initialized")

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 사용내역서 전처리"""
        logging.debug("PersonalExpenseProcessor: Starting preprocessing")
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 아이템 변환"""
        if "expense_items" not in slots or not isinstance(slots["expense_items"], list):
            logging.debug("PersonalExpenseProcessor: No expense_items to process")
            return slots

        logging.info(
            f"PersonalExpenseProcessor: Processing {len(slots['expense_items'])} expense items"
        )

        # 1. 분류 매핑 적용
        updated_items = self.field_converter.process_expense_category_mapping(
            slots["expense_items"]
        )
        slots["expense_items"] = updated_items

        # 2. HTML 필드로 분해
        decomposed_fields = self.item_converter.decompose_expense_items(updated_items)
        slots.update(decomposed_fields)

        logging.info(
            f"PersonalExpenseProcessor: Generated {len(decomposed_fields)} HTML fields from expense items"
        )
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 사용내역서 후처리"""
        # 총액 필드 추가 검증
        if "total_expense_amount" in slots:
            logging.info(
                f"PersonalExpenseProcessor: Total expense amount calculated: {slots['total_expense_amount']}"
            )

        return slots

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """개인 경비 아이템 내 날짜 변환"""
        if "expense_items" not in slots or not isinstance(slots["expense_items"], list):
            return slots

        logging.info(
            f"PersonalExpenseProcessor: Converting dates in {len(slots['expense_items'])} expense items"
        )

        # expense_date 필드 변환
        updated_items = self.date_converter.convert_item_dates(
            slots["expense_items"], "expense_date", current_date_iso
        )
        slots["expense_items"] = updated_items

        return slots
