"""구매 품의서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor
import logging
import json


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
        """구매 품의서 아이템 날짜 변환"""
        if "items" not in slots or not isinstance(slots["items"], list):
            return slots

        return self.item_converter.convert_item_delivery_dates(slots, current_date_iso)

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

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """구매 품의서 폼 데이터를 API Payload로 변환"""
        logging.info("PurchaseApprovalProcessor: Converting form data to API payload")

        payload = {
            "mstPid": "7",
            "aprvNm": form_data.get("title", "구매 품의서"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("purpose", "구매 품의서"),
            "apdInfo": json.dumps(
                {
                    "delivery_location": form_data.get("delivery_location", ""),
                    "payment_terms": form_data.get("payment_terms", ""),
                    "attached_files_description": form_data.get(
                        "attached_files_description", ""
                    ),
                    "total_purchase_amount": form_data.get("total_purchase_amount", 0),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # --- amountList 구성 (구매 품목) ---
        items_source = []
        if "purchase_items" in form_data and isinstance(
            form_data["purchase_items"], list
        ):
            # 최신 프론트엔드에서는 purchase_items 배열을 사용
            for p in form_data["purchase_items"]:
                # 프론트엔드 구조를 items 구조로 맞춰 변환
                items_source.append(
                    {
                        "item_name": p.get("item_name"),
                        "item_spec": p.get("item_spec"),
                        "item_quantity": p.get("item_quantity"),
                        "item_unit_price": p.get("item_unit_price"),
                        "item_total_price": p.get("item_total_price"),
                        "item_delivery_date": p.get("item_delivery_date"),
                        "item_supplier": p.get("item_supplier"),
                        "item_notes": p.get("item_notes"),
                    }
                )
        elif "items" in form_data and isinstance(form_data["items"], list):
            items_source = form_data["items"]

        if items_source:
            for item in items_source:
                item_name = item.get("item_name")
                if not item_name:
                    continue

                item_total_price = item.get("item_total_price", 0)
                item_quantity = item.get("item_quantity", 0)

                adit_info = {
                    "spec": item.get("item_spec", ""),
                    "unitPrice": item.get("item_unit_price", 0),
                    "supplier": item.get("item_supplier", ""),
                }

                payload["amountList"].append(
                    {
                        "useYmd": item.get("item_delivery_date")
                        or form_data.get("draft_date", ""),
                        "dvNm": item_name,
                        "useRsn": item.get("item_notes", ""),
                        "qnty": (
                            int(item_quantity) if str(item_quantity).isdigit() else 0
                        ),
                        "amt": (
                            int(item_total_price)
                            if str(item_total_price).isdigit()
                            else 0
                        ),
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )

        # 결재라인 정보 추가
        if "approvers" in form_data and form_data["approvers"]:
            for approver in form_data["approvers"]:
                payload["lineList"].append(
                    {
                        "aprvPslId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("PurchaseApprovalProcessor: API payload conversion completed")
        return payload
