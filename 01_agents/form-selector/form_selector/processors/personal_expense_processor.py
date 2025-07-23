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
from ..utils import parse_relative_date_to_iso


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

            for i, item in enumerate(items[:3], 1):  # 최대 3개 항목
                result[f"expense_date_{i}"] = item.get("expense_date", "")
                result[f"expense_category_{i}"] = (
                    self.field_converter.map_expense_category_to_value(
                        item.get("expense_category", "")
                    )
                )
                result[f"expense_amount_{i}"] = item.get("expense_amount", 0)
                result[f"expense_description_{i}"] = item.get("expense_description", "")
                result[f"expense_notes_{i}"] = item.get("expense_notes", "")

                # 총액 계산
                total_amount += item.get("expense_amount", 0) or 0

            # 처리된 아이템 리스트를 다시 슬롯에 포함
            result["expense_items"] = items

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

        payload = {
            "mstPid": "8",
            "aprvNm": form_data.get("title", "개인 경비 사용 신청"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("purpose", "개인 경비 사용 신청"),
            "apdInfo": json.dumps(
                {
                    "usage_status": form_data.get("usage_status", ""),
                    "total_amount": form_data.get("total_expense_amount", 0),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # amountList 구성 (비용 정산 정보)
        expenses_to_process = []
        if "expense_items" in form_data and isinstance(
            form_data["expense_items"], list
        ):
            expenses_to_process = form_data["expense_items"]

        if expenses_to_process:
            # expense_items 배열 처리
            for expense in expenses_to_process:
                expense_date = expense.get("expense_date")
                if not expense_date:
                    continue

                expense_amount = expense.get("expense_amount", 0)
                expense_category = expense.get("expense_category", "기타")

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
                    "notes": expense.get("expense_notes", ""),
                }

                payload["amountList"].append(
                    {
                        "useYmd": expense_date,
                        "dvNm": dvNm,
                        "useRsn": expense.get("expense_description", ""),
                        "qnty": 1,
                        "amt": (
                            int(expense_amount) if str(expense_amount).isdigit() else 0
                        ),
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )
        else:
            # HTML 필드 형식 처리 (기존 로직)
            for i in range(1, 4):  # 최대 3개 항목
                expense_date = form_data.get(f"expense_date_{i}")
                if not expense_date:
                    continue

                expense_amount = form_data.get(f"expense_amount_{i}", 0)

                adit_info = {
                    "notes": form_data.get(f"expense_notes_{i}", ""),
                }

                payload["amountList"].append(
                    {
                        "useYmd": expense_date,
                        "dvNm": form_data.get(f"expense_category_{i}", "기타"),
                        "useRsn": form_data.get(f"expense_description_{i}", ""),
                        "qnty": 1,
                        "amt": (
                            int(expense_amount) if str(expense_amount).isdigit() else 0
                        ),
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )

        # 결재라인 정보 추가 (service.py에서 이미 ApproverDetail 객체로 변환됨)
        if "approvers" in form_data and form_data["approvers"]:
            for approver in form_data["approvers"]:
                payload["lineList"].append(
                    {
                        "aprvPslId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("PersonalExpenseProcessor: API payload conversion completed")
        return payload
