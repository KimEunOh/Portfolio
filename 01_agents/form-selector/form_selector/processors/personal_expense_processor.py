"""
개인 경비 사용내역서 전용 처리기

개인 경비 사용내역서의 특별한 처리 로직을 담당합니다.
- expense_items 처리
- 분류 매핑
- HTML 필드 분해
"""

import logging
from typing import Dict, Any
import json

from .base_processor import BaseFormProcessor
from ..utils import parse_relative_date_to_iso, convert_keys_to_camel


class PersonalExpenseProcessor(BaseFormProcessor):
    """개인 경비 사용내역서 전용 처리기"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)
        logging.info("PersonalExpenseProcessor initialized")

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 사용내역서 전처리"""
        # expense_items가 있고 statement_date가 없는 경우, 첫 아이템 날짜로 채움
        if (
            "expense_items" in slots
            and slots["expense_items"]
            and not slots.get("statement_date")
        ):
            first_item = slots["expense_items"][0]
            if "expense_date" in first_item and first_item["expense_date"]:
                slots["statement_date"] = first_item["expense_date"]
                logging.info(
                    f"preprocess_slots: Set statement_date to {first_item['expense_date']} from the first expense item."
                )

        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """아이템 처리: expense_items 배열을 HTML 필드로 분해하고 총액 계산"""
        result = slots.copy()

        # 총액 초기화
        total_amount = 0

        if "expense_items" in slots and slots["expense_items"]:
            items = slots["expense_items"]
            mapped_items = []

            for i, item in enumerate(
                items[:30], 1
            ):  # 최대 30개 항목 (퍼블리싱 스캔 범위와 일치)
                mapped_category = self.field_converter.map_expense_category_to_value(
                    item.get("expense_category", "")
                )
                # 플랫 필드에 매핑 값 반영
                result[f"expense_date_{i}"] = item.get("expense_date", "")
                result[f"expense_category_{i}"] = mapped_category
                result[f"expense_amount_{i}"] = item.get("expense_amount", 0)
                result[f"expense_description_{i}"] = item.get("expense_description", "")
                result[f"expense_notes_{i}"] = item.get("expense_notes", "")

                # 총액 계산
                total_amount += item.get("expense_amount", 0) or 0

                # 배열 아이템에도 매핑된 select value를 유지하도록 업데이트
                item_copy = dict(item)
                item_copy["expense_category"] = mapped_category
                mapped_items.append(item_copy)

            # 처리된/매핑된 아이템 리스트를 다시 슬롯에 포함
            result["expense_items"] = mapped_items

        # 계산된 총액을 슬롯에 추가 (기존 값이 없거나 0인 경우)
        if total_amount > 0 and not result.get("total_expense_amount"):
            result["total_expense_amount"] = total_amount

        return result

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 사용내역서 후처리"""
        # 총액 필드 추가 검증
        if "total_expense_amount" in slots:
            logging.info(
                f"PersonalExpenseProcessor: Total expense amount calculated: {slots['total_expense_amount']}"
            )

        return slots

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 신청서 폼 데이터를 API Payload로 변환 (New Spec)"""
        logging.info("PersonalExpenseProcessor: Converting form data to API payload")

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

        def normalize_ymd(value):
            if value is None:
                return ""
            try:
                s = (
                    str(value).trim()
                    if hasattr(str(value), "trim")
                    else str(value).strip()
                )
                if not s:
                    return ""
                s2 = s.replace(".", "-").replace("/", "-")
                try:
                    rel = parse_relative_date_to_iso(s2)
                    if rel:
                        return rel
                except Exception:
                    pass
                from datetime import datetime as _dt

                for fmt in ("%Y-%m-%d", "%Y-%m", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return _dt.strptime(s2, fmt).date().isoformat()
                    except Exception:
                        continue
                if len(s2) == 8 and s2.isdigit():
                    return f"{s2[0:4]}-{s2[4:6]}-{s2[6:8]}"
                return s2
            except Exception:
                return ""

        # 1. form_data에서 필요한 데이터를 가져옵니다 (snake/camel 혼용 수용)
        usage_status_raw = get_any(["usage_status", "usageStatus"], "")
        usage_status_map = {
            "personal_cash": "개인현금",
            "personal_card": "개인카드",
        }
        usage_status_korean = usage_status_map.get(usage_status_raw, usage_status_raw)

        # 2. apdInfo JSON 문자열을 생성합니다 (items 제외)
        apd_info_dict = {
            "usageStatus": usage_status_korean,
            "totalAmount": parse_amount(
                get_any(["total_expense_amount", "totalExpenseAmount"], 0)
            ),
        }
        final_apd_info_str = json.dumps(
            convert_keys_to_camel(apd_info_dict), ensure_ascii=False
        )

        payload = {
            "mstPid": "8",
            "aprvNm": "개인 경비 사용내역서",
            "drafterId": get_any(["drafter_id", "drafterId"], "00009"),
            "docCn": get_any(
                ["expense_reason", "expenseReason"], "개인 경비 사용 신청"
            ),
            "apdInfo": final_apd_info_str,
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # amountList 구성 (비용 정산 정보)
        # form_data에서 expense_items 키로 조회 (snake_case)
        expenses_to_process = form_data.get("expense_items", [])
        # 문자열로 전달된 hidden JSON 방어 처리
        if isinstance(expenses_to_process, str):
            s = expenses_to_process.strip()
            if s.startswith("[{") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    expenses_to_process = parsed if isinstance(parsed, list) else []
                except Exception:
                    expenses_to_process = []
            else:
                expenses_to_process = []
        if not isinstance(expenses_to_process, list):
            expenses_to_process = []
        logging.info(
            f"PersonalExpenseProcessor: expenses_to_process = {expenses_to_process}"
        )

        if expenses_to_process:
            # expenseItems 배열의 각 항목을 camelCase로 변환
            expenses_camel = convert_keys_to_camel(expenses_to_process)
            try:
                expenses_camel = [e for e in expenses_camel if isinstance(e, dict)]
            except Exception:
                expenses_camel = []
            logging.info(f"PersonalExpenseProcessor: expenses_camel = {expenses_camel}")

            # expenseItems 배열 처리
            for expense in expenses_camel:
                # camelCase로 변환된 키로 조회
                expense_date = expense.get("expenseDate")
                if not expense_date:
                    continue

                expense_amount = expense.get("expenseAmount", 0)
                expense_category = expense.get("expenseCategory", "기타")

                # 분류 매핑 (HTML select value -> 한글명)
                category_mapping = {
                    "traffic": "교통비",
                    "accommodation": "숙박비",
                    "meals": "식대",
                    "entertainment": "접대비",
                    "education": "교육훈련비",
                    "supplies": "소모품비",
                    "other": "기타",
                }
                dvNm = category_mapping.get(expense_category, "기타")

                adit_info = {
                    "notes": expense.get("expenseNotes", ""),
                }

                payload["amountList"].append(
                    {
                        "useYmd": normalize_ymd(expense_date),
                        "dvNm": dvNm,
                        "useRsn": expense.get("expenseDescription", ""),
                        "qnty": 1,
                        "amt": parse_amount(expense_amount),
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )
        else:
            # HTML 필드 형식 처리 (후방 호환): snake/camel 혼용 키 모두 수용
            def get_indexed(keys_patterns, idx, default=None):
                for pattern in keys_patterns:
                    key = pattern.format(i=idx)
                    if key in form_data and form_data.get(key) not in (None, ""):
                        return form_data.get(key)
                return default

            for i in range(1, 31):  # 최대 30개 항목
                expense_date = get_indexed(
                    [
                        "expense_date_{i}",
                        "expense_date{i}",
                        "expenseDate_{i}",
                        "expenseDate{i}",
                    ],
                    i,
                    default=None,
                )
                if not expense_date:
                    continue

                expense_amount = get_indexed(
                    [
                        "expense_amount_{i}",
                        "expense_amount{i}",
                        "expenseAmount_{i}",
                        "expenseAmount{i}",
                    ],
                    i,
                    default=0,
                )

                expense_category_val = get_indexed(
                    [
                        "expense_category_{i}",
                        "expense_category{i}",
                        "expenseCategory_{i}",
                        "expenseCategory{i}",
                    ],
                    i,
                    default="",
                )
                # select value(영문)를 한글 카테고리로 변환
                category_mapping = {
                    "traffic": "교통비",
                    "accommodation": "숙박비",
                    "meals": "식대",
                    "entertainment": "접대비",
                    "education": "교육훈련비",
                    "supplies": "소모품비",
                    "other": "기타",
                }
                dv_nm = category_mapping.get(
                    str(expense_category_val or "").strip(), "기타"
                )

                expense_description = get_indexed(
                    [
                        "expense_description_{i}",
                        "expense_description{i}",
                        "expenseDescription_{i}",
                        "expenseDescription{i}",
                    ],
                    i,
                    default="",
                )
                expense_notes = get_indexed(
                    [
                        "expense_notes_{i}",
                        "expense_notes{i}",
                        "expenseNotes_{i}",
                        "expenseNotes{i}",
                    ],
                    i,
                    default="",
                )

                adit_info = {"notes": expense_notes or ""}

                payload["amountList"].append(
                    {
                        "useYmd": normalize_ymd(expense_date),
                        "dvNm": dv_nm,
                        "useRsn": expense_description or "",
                        "qnty": 1,
                        "amt": parse_amount(expense_amount),
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )

        # 결재라인 정보 추가 (service.py에서 이미 ApproverDetail 객체로 변환됨)
        if "approvers" in form_data and form_data["approvers"]:
            for approver in form_data["approvers"]:
                payload["lineList"].append(
                    {
                        "aprvPsId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("PersonalExpenseProcessor: API payload conversion completed")
        return payload
