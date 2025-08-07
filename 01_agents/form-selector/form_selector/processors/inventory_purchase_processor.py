"""비품/소모품 구입내역서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor
import logging
import json
from ..utils import parse_relative_date_to_iso, convert_keys_to_camel


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

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """비품/소모품 구입내역서 후처리"""
        return slots

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """비품/소모품 구입내역서 폼 데이터를 API Payload로 변환"""
        logging.info("InventoryPurchaseProcessor: Converting form data to API payload")

        # 1. form_data에서 데이터를 가져옵니다 (snake_case 키 사용).
        items_snake = form_data.get("items", [])

        # 2. items 리스트의 키를 camelCase로 변환합니다.
        items_camel = convert_keys_to_camel(items_snake)

        # 3. 변환된 데이터를 사용하여 apdInfo JSON 문자열을 생성합니다.
        apd_info_dict = {
            "requestDate": form_data.get("request_date", ""),
            "totalAmount": form_data.get("total_amount", 0),
            "paymentMethod": form_data.get("payment_method", "corporate_card"),
        }
        final_apd_info_str = json.dumps(
            convert_keys_to_camel(apd_info_dict), ensure_ascii=False
        )

        # 4. 기본 페이로드 구조를 설정합니다.
        payload = {
            "mstPid": "6",
            "aprvNm": "비품/소모품 구입내역서",
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("purpose", "비품/소모품 구입내역서"),
            "apdInfo": final_apd_info_str,
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # 5. amountList를 구성합니다 (camelCase로 변환된 items_camel 사용).
        request_date = form_data.get("request_date", "")

        if items_camel:
            for item in items_camel:
                item_name = item.get("itemName")
                if not item_name:
                    continue

                item_quantity = item.get("itemQuantity", 0)
                item_unit_price = item.get("itemUnitPrice", 0)
                item_total_price = item.get("itemTotalPrice", 0)

                adit_info = {
                    "unitPrice": (
                        int(item_unit_price) if str(item_unit_price).isdigit() else 0
                    )
                }

                payload["amountList"].append(
                    {
                        "useYmd": request_date,
                        "dvNm": item_name,
                        "useRsn": item.get("itemPurpose", ""),
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
        else:
            # Fallback for older format (HTML 필드 직접 참조)
            for i in range(1, 7):
                item_name = form_data.get(f"itemName_{i}")
                if not item_name:
                    continue

                item_quantity = form_data.get(f"itemQuantity_{i}", 0)
                item_unit_price = form_data.get(f"itemUnitPrice_{i}", 0)
                item_total_price = form_data.get(f"itemTotalPrice_{i}", 0)

                adit_info = {
                    "unitPrice": (
                        int(item_unit_price) if str(item_unit_price).isdigit() else 0
                    )
                }

                payload["amountList"].append(
                    {
                        "useYmd": request_date,
                        "dvNm": item_name,
                        "useRsn": form_data.get(f"itemPurpose_{i}", ""),
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
                        "aprvPsId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("InventoryPurchaseProcessor: API payload conversion completed")
        return payload
