"""비품/소모품 구입내역서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor
import logging
import json


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
        """비품구입 아이템 날짜 변환

        비품구입은 아이템이 없으므로 날짜 변환하지 않습니다.
        """
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

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """비품/소모품 구입내역서 폼 데이터를 API Payload로 변환"""
        logging.info("InventoryPurchaseProcessor: Converting form data to API payload")

        payload = {
            "mstPid": "6",
            "aprvNm": form_data.get("title", "비품/소모품 구입내역서"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("purpose", "비품/소모품 구입내역서"),
            "apdInfo": json.dumps(
                {
                    "request_date": form_data.get("request_date", ""),
                    "purpose": form_data.get("purpose", ""),
                    "total_amount": form_data.get("total_amount", 0),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # amountList 구성 (구입 내역)
        if "items" in form_data and isinstance(form_data["items"], list):
            for item in form_data["items"]:
                item_name = item.get("item_name")
                if not item_name:
                    continue

                item_quantity = item.get("item_quantity", 0)
                item_unit_price = item.get("item_unit_price", 0)
                item_total_price = item.get("item_total_price", 0)

                adit_info = {
                    "unitPrice": (
                        int(item_unit_price) if str(item_unit_price).isdigit() else 0
                    )
                }

                payload["amountList"].append(
                    {
                        "useYmd": form_data.get("request_date", ""),
                        "dvNm": item_name,
                        "useRsn": item.get("item_purpose", ""),
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
            # Fallback for older format if "items" list is not present
            for i in range(1, 7):  # 최대 6개 항목
                item_name = form_data.get(f"item_name_{i}")
                if not item_name:
                    continue

                item_quantity = form_data.get(f"item_quantity_{i}", 0)
                item_unit_price = form_data.get(f"item_unit_price_{i}", 0)
                item_total_price = form_data.get(f"item_total_price_{i}", 0)

                adit_info = {
                    "unitPrice": (
                        int(item_unit_price) if str(item_unit_price).isdigit() else 0
                    )
                }

                payload["amountList"].append(
                    {
                        "useYmd": form_data.get("request_date", ""),
                        "dvNm": item_name,
                        "useRsn": form_data.get(f"item_purpose_{i}", ""),
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

        logging.info("InventoryPurchaseProcessor: API payload conversion completed")
        return payload
