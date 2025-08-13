"""비품/소모품 구입내역서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor
import logging
import json
from datetime import datetime
from ..utils import parse_relative_date_to_iso, convert_keys_to_camel


class InventoryPurchaseProcessor(BaseFormProcessor):
    """비품/소모품 구입내역서 전용 프로세서

    - 아이템 리스트 분해 (최대 12개)
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

            # 최대 12개 아이템까지 처리
            for i, item in enumerate(items[:12], 1):
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

        # 유틸: 다양한 케이스/형태 지원
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

        # 1. form_data에서 데이터를 가져옵니다 (snake_case 키 사용).
        # 우선순위: purchase_items(충돌 방지용 새 키) > items
        items_snake = form_data.get("purchase_items")
        if items_snake is None:
            items_snake = form_data.get("items", [])
        # 견고화: 문자열 JSON이면 파싱, 리스트가 아니면 무시
        if isinstance(items_snake, str):
            s = items_snake.strip()
            # '[object Object],...' 같은 잘못된 문자열은 무시
            if s.startswith("[{") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        items_snake = parsed
                    else:
                        items_snake = []
                except Exception:
                    items_snake = []
            else:
                items_snake = []
        if not isinstance(items_snake, list):
            items_snake = []

        # 2. items 리스트의 키를 camelCase로 변환합니다.
        items_camel = convert_keys_to_camel(items_snake) if items_snake else []

        # 3. 변환된 데이터를 사용하여 apdInfo JSON 문자열을 생성합니다.
        # 요청일 결정: snake/camel 우선 사용, 없으면 오늘 날짜(YYYY-MM-DD)
        resolved_request_date = get_any(["request_date", "requestDate"], "")
        if not resolved_request_date:
            try:
                resolved_request_date = datetime.now().date().isoformat()
            except Exception:
                resolved_request_date = ""

        apd_info_dict = {
            "requestDate": resolved_request_date,
            "totalAmount": parse_amount(get_any(["total_amount", "totalAmount"], 0)),
            "paymentMethod": get_any(
                ["payment_method", "paymentMethod"], "corporate_card"
            ),
        }
        final_apd_info_str = json.dumps(
            convert_keys_to_camel(apd_info_dict), ensure_ascii=False
        )

        # 4. 기본 페이로드 구조를 설정합니다.
        payload = {
            "mstPid": "6",
            "aprvNm": "비품/소모품 구입내역서",
            # drafterId: snake/camel 모두 수용
            "drafterId": get_any(["drafter_id", "drafterId"], ""),
            "docCn": form_data.get("purpose", "비품/소모품 구입내역서"),
            "apdInfo": final_apd_info_str,
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # 5. amountList를 구성합니다 (camelCase로 변환된 items_camel 사용).
        request_date = resolved_request_date

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
            # Fallback for older/newer format (HTML 필드 직접 참조, 다양한 네이밍 수용)
            def get_indexed(keys_patterns, idx, default=None):
                for pattern in keys_patterns:
                    key = pattern.format(i=idx)
                    if key in form_data and form_data.get(key) not in (None, ""):
                        return form_data.get(key)
                return default

            for i in range(1, 13):  # 최대 12개 항목까지 고려 (퍼블리싱 기준 상한 여유)
                item_name = get_indexed(
                    [
                        "item_name_{i}",  # snake_case with underscore
                        "item_name{i}",  # snake_case with index suffix
                        "itemName{i}",  # camelCase without underscore
                        "itemName_{i}",  # camelCase with underscore
                    ],
                    i,
                    default=None,
                )

                if not item_name:
                    continue

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
                item_unit_price = get_indexed(
                    [
                        "item_unit_price_{i}",
                        "item_unit_price{i}",
                        "itemUnitPrice{i}",
                        "itemUnitPrice_{i}",
                    ],
                    i,
                    default=0,
                )
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
                item_purpose = get_indexed(
                    [
                        "item_purpose_{i}",
                        "item_purpose{i}",
                        "itemPurpose{i}",
                        "itemPurpose_{i}",
                    ],
                    i,
                    default="",
                )

                adit_info = {"unitPrice": parse_amount(item_unit_price)}

                payload["amountList"].append(
                    {
                        "useYmd": request_date,
                        "dvNm": item_name,
                        "useRsn": item_purpose,
                        "qnty": parse_amount(item_quantity),
                        "amt": parse_amount(item_total_price),
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )

        # 안전장치: apdInfo.requestDate가 비어있으면 오늘 날짜로 보정
        try:
            apd = json.loads(payload.get("apdInfo", "{}"))
            rd = apd.get("requestDate")
            if not rd:
                apd["requestDate"] = datetime.now().date().isoformat()
                payload["apdInfo"] = json.dumps(apd, ensure_ascii=False)
        except Exception:
            pass

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
