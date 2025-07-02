"""
연차 신청서 전용 처리기

연차 신청서의 특별한 처리 로직을 담당합니다.
"""

import logging
from typing import Dict, Any

from .base_processor import BaseFormProcessor


class AnnualLeaveProcessor(BaseFormProcessor):
    """연차 신청서 전용 처리기"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)
        logging.info("AnnualLeaveProcessor initialized")

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """연차 신청서 전처리

        연차 신청서는 특별한 전처리가 필요하지 않습니다.
        """
        logging.debug("AnnualLeaveProcessor: No special preprocessing needed")
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """연차 신청서 아이템 변환

        연차 신청서는 아이템 리스트가 없으므로 변환하지 않습니다.
        """
        logging.debug("AnnualLeaveProcessor: No items to convert")
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """연차 신청서 후처리

        연차 신청서는 특별한 후처리가 필요하지 않습니다.
        """
        logging.debug("AnnualLeaveProcessor: No special postprocessing needed")
        return slots

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """연차 신청서 아이템 날짜 변환

        연차 신청서는 아이템이 없으므로 날짜 변환하지 않습니다.
        """
        logging.debug("AnnualLeaveProcessor: No item dates to convert")
        return slots
