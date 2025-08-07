"""구매 품의서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor
import logging
import json
from datetime import datetime

from ..utils import parse_relative_date_to_iso, convert_keys_to_camel


class PurchaseApprovalProcessor(BaseFormProcessor):
    """구매 품의서 전용 처리기"""

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """구매 품의서 전처리"""
        return slots

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str, prefer_past: bool = False
    ) -> Dict[str, Any]:
        """구매 품의서 아이템 날짜 변환"""
        return super().convert_item_dates(slots, current_date_iso, prefer_past)

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
                delivery_date = item.get("item_delivery_request_date") or item.get(
                    "item_delivery_request_date", ""
                )
                result[f"item_delivery_date_{i}"] = delivery_date

                result[f"item_supplier_{i}"] = item.get("item_supplier", "")

                # item_purpose나 item_notes를 item_notes로 매핑
                notes = item.get("item_notes") or item.get("item_purpose", "")
                result[f"item_notes_{i}"] = notes

                # 총액에 추가
                total_amount += item.get("item_total_price", 0) or 0

            # 처리된 아이템 리스트를 슬롯에 다시 포함 (테스트용)
            result["items"] = items

        # 계산된 총액을 슬롯에 추가
        if total_amount > 0 and not result.get("total_purchase_amount"):
            result["total_purchase_amount"] = total_amount

        return result

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """필드 변환: 특별한 필드 변환 없음"""
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """후처리: 빈 필드 기본값 설정 및 지출 사유 자동 생성"""
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
        """구매품의서 폼 데이터를 API Payload로 변환"""
        logging.info("PurchaseApprovalProcessor: Converting form data to API payload")

        # 1. form_data에서 items 리스트를 가져옵니다. (purchase_items 키 사용)
        items_snake = form_data.get("purchase_items", [])
        logging.info(f"PurchaseApprovalProcessor: items_snake = {items_snake}")

        # 2. items 리스트의 키를 camelCase로 변환합니다.
        items_camel = convert_keys_to_camel(items_snake)
        logging.info(f"PurchaseApprovalProcessor: items_camel = {items_camel}")

        # 3. 변환된 데이터를 사용하여 apdInfo JSON 문자열을 생성합니다. (items 제외)
        apd_info_dict = {
            "deliveryLocation": form_data.get("delivery_location", ""),
            "paymentTerms": form_data.get("payment_terms", ""),
            "attachedFilesDescription": form_data.get("attached_files_description", ""),
            "totalPurchaseAmount": form_data.get("total_purchase_amount", 0),
            "specialNotes": form_data.get("special_notes", ""),
        }
        final_apd_info_str = json.dumps(
            convert_keys_to_camel(apd_info_dict), ensure_ascii=False
        )

        # 4. 기본 페이로드 구조를 설정합니다.
        payload = {
            "mstPid": "7",
            "aprvNm": "구매 품의서",
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("purpose", "구매 품의서"),
            "apdInfo": final_apd_info_str,
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # 5. amountList를 구성합니다 (camelCase로 변환된 items_camel 사용).
        draft_date = form_data.get("draft_date", "")
        logging.info(
            f"PurchaseApprovalProcessor: Processing {len(items_camel) if items_camel else 0} items for amountList"
        )

        if items_camel:
            for item in items_camel:
                item_name = item.get("itemName")
                logging.info(f"PurchaseApprovalProcessor: Processing item: {item_name}")
                if not item_name or item_name == "SLOT_NOT_FOUND_OR_UNDEFINED":
                    continue

                item_total_price = item.get("itemTotalPrice", 0)
                item_quantity = item.get("itemQuantity", 0)

                adit_info = {
                    "spec": item.get("itemSpec", ""),
                    "unitPrice": item.get("itemUnitPrice", 0),
                    "supplier": item.get("itemSupplier", ""),
                }

                amount_item = {
                    "useYmd": item.get("itemDeliveryDate") or draft_date,
                    "dvNm": item_name,
                    "useRsn": item.get("itemNotes", ""),
                    "qnty": (int(item_quantity) if str(item_quantity).isdigit() else 0),
                    "amt": (
                        int(item_total_price) if str(item_total_price).isdigit() else 0
                    ),
                    "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                }
                payload["amountList"].append(amount_item)
                logging.info(
                    f"PurchaseApprovalProcessor: Added amount item: {amount_item}"
                )
        else:
            logging.info(
                "PurchaseApprovalProcessor: No items_camel, trying fallback..."
            )
            # Fallback for older format (HTML 필드 직접 참조)
            for i in range(1, 4):
                item_name = form_data.get(f"itemName_{i}")
                if not item_name or item_name == "SLOT_NOT_FOUND_OR_UNDEFINED":
                    continue

                item_total_price = form_data.get(f"itemTotalPrice_{i}", 0)
                item_quantity = form_data.get(f"itemQuantity_{i}", 0)

                adit_info = {
                    "spec": form_data.get(f"itemSpec_{i}", ""),
                    "unitPrice": form_data.get(f"itemUnitPrice_{i}", 0),
                    "supplier": form_data.get(f"itemSupplier_{i}", ""),
                }

                amount_item = {
                    "useYmd": form_data.get(f"itemDeliveryDate_{i}") or draft_date,
                    "dvNm": item_name,
                    "useRsn": form_data.get(f"itemNotes_{i}", ""),
                    "qnty": (int(item_quantity) if str(item_quantity).isdigit() else 0),
                    "amt": (
                        int(item_total_price) if str(item_total_price).isdigit() else 0
                    ),
                    "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                }
                payload["amountList"].append(amount_item)
                logging.info(
                    f"PurchaseApprovalProcessor: Added fallback amount item: {amount_item}"
                )

        logging.info(
            f"PurchaseApprovalProcessor: Final amountList length: {len(payload['amountList'])}"
        )

        # 결재라인 정보 추가
        if "approvers" in form_data and form_data["approvers"]:
            for approver in form_data["approvers"]:
                payload["lineList"].append(
                    {
                        "aprvPsId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("PurchaseApprovalProcessor: API payload conversion completed")
        return payload
