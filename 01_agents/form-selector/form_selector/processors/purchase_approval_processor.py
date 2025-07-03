"""구매 품의서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor


class PurchaseApprovalProcessor(BaseFormProcessor):
    """구매 품의서 전용 프로세서

    - 복잡한 아이템 구조 처리 (최대 3개)
    - 납기일 변환 (item_delivery_request_date → item_delivery_date)
    - 총액 계산
    - 8개 필드 per 아이템: name, spec, quantity, unit_price, total_price, delivery_date, supplier, notes
    """

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """전처리: 기본값 설정"""
        processed = slots.copy()

        # 기본 제목 설정
        if not processed.get("title"):
            processed["title"] = "구매 품의서"

        return processed

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """아이템 내 납기일 변환"""
        from ..utils import parse_relative_date_to_iso

        result = slots.copy()

        # items 배열 내의 납기일 변환
        if "items" in result and result["items"]:
            for item in result["items"]:
                # item_delivery_request_date를 item_delivery_date로 변환
                if (
                    "item_delivery_request_date" in item
                    and item["item_delivery_request_date"]
                ):
                    delivery_date = parse_relative_date_to_iso(
                        item["item_delivery_request_date"], current_date_iso
                    )
                    if delivery_date:
                        item["item_delivery_date"] = delivery_date

        return result

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """아이템 처리: items 배열을 HTML 필드로 분해하고 총액 계산"""
        result = slots.copy()

        # 총액 초기화
        total_amount = 0

        # items 배열이 있는 경우 HTML 필드로 분해
        if "items" in slots and slots["items"]:
            items = slots["items"]

            # 최대 3개 아이템까지 처리
            for i, item in enumerate(items[:3], 1):
                result[f"item_name_{i}"] = item.get("item_name", "")
                result[f"item_spec_{i}"] = item.get("item_spec", "")
                result[f"item_quantity_{i}"] = item.get("item_quantity", 0)
                result[f"item_unit_price_{i}"] = item.get("item_unit_price", 0)
                result[f"item_total_price_{i}"] = item.get("item_total_price", 0)

                # 납기일 처리 (변환된 item_delivery_date 우선, 없으면 원본 사용)
                delivery_date = item.get("item_delivery_date") or item.get(
                    "item_delivery_request_date", ""
                )
                result[f"item_delivery_date_{i}"] = delivery_date

                result[f"item_supplier_{i}"] = item.get("item_supplier", "")

                # item_purpose나 item_notes를 item_notes로 매핑
                notes = item.get("item_notes") or item.get("item_purpose", "")
                result[f"item_notes_{i}"] = notes

                # 총액에 추가
                total_amount += item.get("item_total_price", 0)

        # 직접 제공된 total_purchase_amount가 있으면 우선 사용
        if (
            "total_purchase_amount" in slots
            and slots["total_purchase_amount"] is not None
        ):
            result["total_purchase_amount"] = slots["total_purchase_amount"]
        else:
            result["total_purchase_amount"] = total_amount

        return result

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """필드 변환: 특별한 필드 변환 없음"""
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """후처리: 빈 필드 기본값 설정"""
        processed = slots.copy()

        # 기본값 설정
        if not processed.get("payment_terms"):
            processed["payment_terms"] = ""

        if not processed.get("delivery_location"):
            processed["delivery_location"] = ""

        if not processed.get("attached_files_description"):
            processed["attached_files_description"] = ""

        if not processed.get("special_notes"):
            processed["special_notes"] = ""

        return processed
