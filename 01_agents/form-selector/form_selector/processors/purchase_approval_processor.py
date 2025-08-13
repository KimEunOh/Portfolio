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

            # 최대 12개 아이템까지 처리 (퍼블리싱/어댑터 상한과 일치)
            for i, item in enumerate(items[:12], 1):
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

        # 유틸: 혼용 키 수용 및 금액 파싱
        def get_any(keys, default=""):
            for k in keys:
                if k in form_data and form_data.get(k) not in (None, ""):
                    return form_data.get(k)
            return default

        def parse_amount(value) -> int:
            try:
                if value is None:
                    return 0
                if isinstance(value, (int, float)):
                    return int(value)
                s = str(value)
                digits = "".join(ch for ch in s if ch.isdigit())
                return int(digits) if digits else 0
            except Exception:
                return 0

        def normalize_ymd(value: Any) -> str:
            """다양한 날짜 입력을 YYYY-MM-DD로 통일. 실패 시 원문 반환 또는 빈 문자열."""
            if value is None:
                return ""
            try:
                s = str(value).strip()
                if not s:
                    return ""
                # 구분자 통일
                s2 = s.replace(".", "-").replace("/", "-")
                # 상대 날짜 파서 시도
                try:
                    rel = parse_relative_date_to_iso(s2)
                    if rel:
                        return rel
                except Exception:
                    pass
                # 명시적 포맷 파싱 시도
                from datetime import datetime as _dt

                for fmt in ("%Y-%m-%d", "%Y-%m", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return _dt.strptime(s2, fmt).date().isoformat()
                    except Exception:
                        continue
                # 8자리 숫자 형태(YYYYMMDD)
                if len(s2) == 8 and s2.isdigit():
                    return f"{s2[0:4]}-{s2[4:6]}-{s2[6:8]}"
                return s2
            except Exception:
                return ""

        # 1. form_data에서 items 리스트를 가져옵니다. (purchase_items 키 사용)
        items_snake = form_data.get("purchase_items", [])
        logging.info(f"PurchaseApprovalProcessor: items_snake = {items_snake}")
        # 문자열로 전달된 hidden JSON 방어 처리
        if isinstance(items_snake, str):
            s = items_snake.strip()
            if s.startswith("[{") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    items_snake = parsed if isinstance(parsed, list) else []
                except Exception:
                    items_snake = []
            else:
                items_snake = []
        if not isinstance(items_snake, list):
            items_snake = []

        # 2. items 리스트의 키를 camelCase로 변환합니다.
        items_camel = convert_keys_to_camel(items_snake) if items_snake else []
        logging.info(f"PurchaseApprovalProcessor: items_camel = {items_camel}")
        # 리스트 내 원소 타입 방어: dict가 아닌 값은 제거
        if items_camel and any(not isinstance(it, dict) for it in items_camel):
            try:
                items_camel = [it for it in items_camel if isinstance(it, dict)]
            except Exception:
                items_camel = []

        # 3. 변환된 데이터를 사용하여 apdInfo JSON 문자열을 생성합니다. (items 제외)
        apd_info_dict = {
            "deliveryLocation": get_any(["delivery_location", "deliveryLocation"], ""),
            "paymentTerms": get_any(["payment_terms", "paymentTerms"], ""),
            "attachedFilesDescription": get_any(
                ["attached_files_description", "attachedFilesDescription"], ""
            ),
            "totalPurchaseAmount": parse_amount(
                get_any(["total_purchase_amount", "totalPurchaseAmount"], 0)
            ),
            "specialNotes": get_any(["special_notes", "specialNotes"], ""),
        }
        final_apd_info_str = json.dumps(
            convert_keys_to_camel(apd_info_dict), ensure_ascii=False
        )

        # 4. 기본 페이로드 구조를 설정합니다.
        payload = {
            "mstPid": "7",
            "aprvNm": "구매 품의서",
            "drafterId": get_any(["drafter_id", "drafterId"], "00009"),
            "docCn": get_any(["purpose", "docCn"], "구매 품의서"),
            "apdInfo": final_apd_info_str,
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # 5. amountList를 구성합니다 (camelCase로 변환된 items_camel 사용).
        draft_date = normalize_ymd(get_any(["draft_date", "draftDate"], ""))
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
                    "useYmd": normalize_ymd(item.get("itemDeliveryDate") or draft_date),
                    "dvNm": item_name,
                    "useRsn": item.get("itemNotes", ""),
                    "qnty": parse_amount(item_quantity),
                    "amt": parse_amount(item_total_price),
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

            # Fallback for older/newer format (HTML 필드 직접 참조, 다양한 네이밍 수용)
            def get_indexed(keys_patterns, idx, default=None):
                for pattern in keys_patterns:
                    key = pattern.format(i=idx)
                    if key in form_data and form_data.get(key) not in (None, ""):
                        return form_data.get(key)
                return default

            for i in range(1, 13):
                item_name = get_indexed(
                    ["item_name_{i}", "item_name{i}", "itemName{i}", "itemName_{i}"],
                    i,
                    default=None,
                )
                if not item_name or item_name == "SLOT_NOT_FOUND_OR_UNDEFINED":
                    continue

                item_total_price = get_indexed(
                    [
                        "item_total_price_{i}",
                        "item_total_price{i}",
                        "itemTotalPrice{i}",
                        "itemTotalPrice_{i}",
                    ],
                    i,
                    default=0,
                )
                item_quantity = get_indexed(
                    [
                        "item_quantity_{i}",
                        "item_quantity{i}",
                        "itemQuantity{i}",
                        "itemQuantity_{i}",
                    ],
                    i,
                    default=0,
                )

                adit_info = {
                    "spec": get_indexed(
                        [
                            "item_spec_{i}",
                            "item_spec{i}",
                            "itemSpec{i}",
                            "itemSpec_{i}",
                        ],
                        i,
                        default="",
                    ),
                    "unitPrice": parse_amount(
                        get_indexed(
                            [
                                "item_unit_price_{i}",
                                "item_unit_price{i}",
                                "itemUnitPrice{i}",
                                "itemUnitPrice_{i}",
                            ],
                            i,
                            default=0,
                        )
                    ),
                    "supplier": get_indexed(
                        [
                            "item_supplier_{i}",
                            "item_supplier{i}",
                            "itemSupplier{i}",
                            "itemSupplier_{i}",
                        ],
                        i,
                        default="",
                    ),
                }

                amount_item = {
                    "useYmd": normalize_ymd(
                        get_indexed(
                            [
                                "item_delivery_date_{i}",
                                "item_delivery_date{i}",
                                "itemDeliveryDate{i}",
                                "itemDeliveryDate_{i}",
                            ],
                            i,
                            default=None,
                        )
                        or draft_date
                    ),
                    "dvNm": item_name,
                    "useRsn": get_indexed(
                        [
                            "item_notes_{i}",
                            "item_notes{i}",
                            "itemNotes{i}",
                            "itemNotes_{i}",
                        ],
                        i,
                        default="",
                    ),
                    "qnty": parse_amount(item_quantity),
                    "amt": parse_amount(item_total_price),
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
