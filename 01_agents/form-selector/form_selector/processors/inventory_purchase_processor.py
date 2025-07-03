"""비품/소모품 구입내역서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor


class InventoryPurchaseProcessor(BaseFormProcessor):
    """비품/소모품 구입내역서 전용 프로세서

    - 아이템 리스트 분해 (최대 6개)
    - 총액 계산
    - 날짜 변환
    """

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """전처리: 기본값 설정"""
        processed = slots.copy()

        # 기본 제목 설정
        if not processed.get("title"):
            processed["title"] = "비품/소모품 구입 요청"

        return processed

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """아이템 날짜 변환: 비품 구입내역서는 개별 아이템 날짜가 없으므로 기본 처리"""
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """아이템 처리: items 배열을 HTML 필드로 분해하고 총액 계산"""
        result = slots.copy()

        # 총액 초기화
        total_amount = 0

        # items 배열이 있는 경우 HTML 필드로 분해
        if "items" in slots and slots["items"]:
            items = slots["items"]

            # 최대 6개 아이템까지 처리
            for i, item in enumerate(items[:6], 1):
                result[f"item_name_{i}"] = item.get("item_name", "")
                result[f"item_quantity_{i}"] = item.get("item_quantity", 0)
                result[f"item_unit_price_{i}"] = item.get("item_unit_price", 0)
                result[f"item_total_price_{i}"] = item.get("item_total_price", 0)
                result[f"item_purpose_{i}"] = item.get(
                    "item_notes", ""
                )  # item_notes -> item_purpose

                # 총액에 추가
                total_amount += item.get("item_total_price", 0)

        # 직접 제공된 total_amount가 있으면 우선 사용
        if "total_amount" in slots and slots["total_amount"] is not None:
            result["total_amount"] = slots["total_amount"]
        else:
            result["total_amount"] = total_amount

        return result

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """필드 변환: 특별한 필드 변환 없음"""
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """후처리: 빈 필드 기본값 설정"""
        processed = slots.copy()

        # 기본값 설정
        if not processed.get("payment_method"):
            processed["payment_method"] = ""

        if not processed.get("notes"):
            processed["notes"] = ""

        return processed
