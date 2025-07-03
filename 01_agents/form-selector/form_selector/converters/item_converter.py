"""
아이템 변환기 클래스

service.py에서 분산되어 있던 아이템 리스트 처리 로직을 통합 관리합니다.
"""

import logging
from typing import Dict, Any, List

from ..utils import parse_relative_date_to_iso


class ItemConverter:
    """아이템 리스트 변환을 전담하는 클래스"""

    def convert_card_usage_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """법인카드 사용 내역 아이템 날짜 변환"""
        if "card_usage_items" not in slots or not isinstance(
            slots["card_usage_items"], list
        ):
            return slots

        result = slots.copy()

        for item in result["card_usage_items"]:
            if isinstance(item, dict) and "usage_date" in item and item["usage_date"]:
                original_date = item["usage_date"]
                parsed_date = parse_relative_date_to_iso(
                    original_date, current_date_iso
                )
                if parsed_date:
                    item["usage_date"] = parsed_date
                    logging.debug(
                        f"Card usage date converted: '{original_date}' -> '{parsed_date}'"
                    )

        logging.info(
            f"Converted dates in {len(result['card_usage_items'])} card usage items"
        )
        return result

    def convert_expense_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """개인 경비 아이템 날짜 변환"""
        if "expense_items" not in slots or not isinstance(slots["expense_items"], list):
            return slots

        result = slots.copy()

        for item in result["expense_items"]:
            if (
                isinstance(item, dict)
                and "expense_date" in item
                and item["expense_date"]
            ):
                original_date = item["expense_date"]
                parsed_date = parse_relative_date_to_iso(
                    original_date, current_date_iso
                )
                if parsed_date:
                    item["expense_date"] = parsed_date
                    logging.debug(
                        f"Expense date converted: '{original_date}' -> '{parsed_date}'"
                    )

        logging.info(f"Converted dates in {len(result['expense_items'])} expense items")
        return result

    def convert_item_delivery_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """구매 품의서 아이템 납기일 변환"""
        if "items" not in slots or not isinstance(slots["items"], list):
            return slots

        result = slots.copy()

        for item in result["items"]:
            if isinstance(item, dict):
                # item_delivery_request_date를 item_delivery_date로 변환
                if (
                    "item_delivery_request_date" in item
                    and item["item_delivery_request_date"]
                ):
                    original_date = item["item_delivery_request_date"]
                    parsed_date = parse_relative_date_to_iso(
                        original_date, current_date_iso
                    )
                    if parsed_date:
                        item["item_delivery_date"] = parsed_date
                        logging.debug(
                            f"Item delivery date converted: '{original_date}' -> '{parsed_date}'"
                        )
                        # 원본 키 삭제 (변환 완료 후)
                        del item["item_delivery_request_date"]

        logging.info(
            f"Converted delivery dates in {len(result['items'])} purchase items"
        )
        return result

    def decompose_to_html_fields(
        self,
        items: List[Dict[str, Any]],
        prefix: str,
        max_count: int,
        field_mapping: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """아이템 배열을 개별 HTML 필드로 분해"""
        decomposed_fields = {}
        field_mapping = field_mapping or {}

        for i, item in enumerate(items[:max_count], 1):
            if isinstance(item, dict):
                for field_name, field_value in item.items():
                    # 필드 매핑이 있으면 적용
                    mapped_field_name = field_mapping.get(field_name, field_name)
                    decomposed_fields[f"{mapped_field_name}_{i}"] = field_value

        logging.info(
            f"Decomposed {len(items)} items to HTML fields with prefix '{prefix}'"
        )
        return decomposed_fields

    def calculate_totals(self, items: List[Dict[str, Any]], amount_field: str) -> int:
        """아이템들의 총액 계산"""
        total = 0

        for item in items:
            if isinstance(item, dict) and amount_field in item:
                try:
                    amount = item[amount_field]
                    if isinstance(amount, (int, float)):
                        total += int(amount)
                    elif isinstance(amount, str) and amount.isdigit():
                        total += int(amount)
                except (ValueError, TypeError):
                    logging.warning(f"Invalid amount value in item: {amount}")
                    continue

        logging.info(f"Calculated total amount: {total} from {len(items)} items")
        return total

    def map_item_fields(
        self, items: List[Dict[str, Any]], field_mapping: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """아이템 필드명 매핑 (item_purpose → item_notes 등)"""
        mapped_items = []

        for item in items:
            if isinstance(item, dict):
                mapped_item = {**item}  # 원본 보존

                for old_field, new_field in field_mapping.items():
                    if old_field in mapped_item:
                        # 새 필드가 없거나 비어있을 경우에만 매핑
                        if new_field not in mapped_item or not mapped_item[new_field]:
                            mapped_item[new_field] = mapped_item[old_field]
                            logging.debug(
                                f"Item field mapped: '{old_field}' -> '{new_field}'"
                            )

                        # 원본 필드는 값이 복사되었을 경우에만 삭제
                        if (
                            new_field in mapped_item
                            and mapped_item[old_field] == mapped_item[new_field]
                        ):
                            del mapped_item[old_field]

                mapped_items.append(mapped_item)
            else:
                mapped_items.append(item)

        logging.info(f"Applied field mapping to {len(items)} items")
        return mapped_items

    def process_purchase_items(
        self, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """구매 품의서 아이템 특별 처리"""
        field_mapping = {
            "item_delivery_request_date": "item_delivery_date",
            "item_purpose": "item_notes",
        }
        return self.map_item_fields(items, field_mapping)

    def decompose_corporate_card_items(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """법인카드 아이템을 HTML 필드로 분해"""
        fields = {}

        # 개별 필드 분해
        for i, item in enumerate(items[:6], 1):  # 최대 6개 항목
            fields[f"usage_date_{i}"] = item.get("usage_date", "")
            fields[f"usage_category_{i}"] = item.get("usage_category", "")
            fields[f"merchant_name_{i}"] = item.get("usage_description", "")
            fields[f"usage_amount_{i}"] = item.get("usage_amount", "")
            fields[f"usage_notes_{i}"] = item.get("usage_notes", "")

        # 총 금액 계산
        total_amount = self.calculate_totals(items, "usage_amount")
        fields["total_usage_amount"] = total_amount
        fields["total_amount_header"] = total_amount

        return fields

    def decompose_inventory_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """비품/소모품 아이템을 HTML 필드로 분해"""
        fields = {}

        # 개별 필드 분해
        for i, item in enumerate(items[:6], 1):  # 최대 6개 항목
            fields[f"item_name_{i}"] = item.get("item_name", "")
            fields[f"item_quantity_{i}"] = item.get("item_quantity", "")
            fields[f"item_unit_price_{i}"] = item.get("item_unit_price", "")
            fields[f"item_total_price_{i}"] = item.get("item_total_price", "")
            fields[f"item_purpose_{i}"] = item.get("item_notes", "")

        # 총 금액 계산
        total_amount = self.calculate_totals(items, "item_total_price")
        fields["total_amount"] = total_amount

        return fields

    def decompose_expense_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """개인 경비 아이템을 HTML 필드로 분해"""
        fields = {}

        # 개별 필드 분해
        for i, item in enumerate(items[:3], 1):  # 최대 3개 항목
            fields[f"expense_date_{i}"] = item.get("expense_date", "")
            fields[f"expense_category_{i}"] = item.get("expense_category", "")
            fields[f"expense_description_{i}"] = item.get("expense_description", "")
            fields[f"expense_amount_{i}"] = item.get("expense_amount", "")
            fields[f"expense_notes_{i}"] = item.get("expense_notes", "")

        # 총 금액 계산
        total_amount = self.calculate_totals(items, "expense_amount")
        fields["total_expense_amount"] = total_amount
        fields["total_amount_header"] = total_amount

        return fields

    def decompose_purchase_approval_items(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """구매 품의서 아이템을 HTML 필드로 분해"""
        fields = {}

        # 개별 필드 분해
        for i, item in enumerate(items[:3], 1):  # 최대 3개 항목
            fields[f"item_name_{i}"] = item.get("item_name", "")
            fields[f"item_spec_{i}"] = item.get("item_spec", "")
            fields[f"item_quantity_{i}"] = item.get("item_quantity", "")
            fields[f"item_unit_price_{i}"] = item.get("item_unit_price", "")
            fields[f"item_total_price_{i}"] = item.get("item_total_price", "")
            fields[f"item_delivery_date_{i}"] = item.get(
                "item_delivery_date", item.get("item_delivery_request_date", "")
            )
            fields[f"item_supplier_{i}"] = item.get("item_supplier", "")
            fields[f"item_notes_{i}"] = item.get(
                "item_notes", item.get("item_purpose", "")
            )

        # 총 금액 계산
        total_amount = self.calculate_totals(items, "item_total_price")
        fields["total_purchase_amount"] = total_amount

        return fields
