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


class PersonalExpenseProcessor(BaseFormProcessor):
    """개인 경비 사용내역서 전용 처리기"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)
        logging.info("PersonalExpenseProcessor initialized")

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 사용내역서 전처리"""
        logging.debug("PersonalExpenseProcessor: Starting preprocessing")
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 아이템 변환"""
        if "expense_items" not in slots or not isinstance(slots["expense_items"], list):
            logging.debug("PersonalExpenseProcessor: No expense_items to process")
            return slots

        logging.info(
            f"PersonalExpenseProcessor: Processing {len(slots['expense_items'])} expense items"
        )

        # 1. 분류 매핑 적용
        updated_items = self.field_converter.process_expense_category_mapping(
            slots["expense_items"]
        )
        slots["expense_items"] = updated_items

        # 2. HTML 필드로 분해
        decomposed_fields = self.item_converter.decompose_expense_items(updated_items)
        slots.update(decomposed_fields)

        logging.info(
            f"PersonalExpenseProcessor: Generated {len(decomposed_fields)} HTML fields from expense items"
        )
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 사용내역서 후처리"""
        # 총액 필드 추가 검증
        if "total_expense_amount" in slots:
            logging.info(
                f"PersonalExpenseProcessor: Total expense amount calculated: {slots['total_expense_amount']}"
            )

        return slots

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """개인 경비 아이템 날짜 변환"""
        if "expense_items" not in slots or not isinstance(slots["expense_items"], list):
            return slots

        return self.item_converter.convert_expense_item_dates(slots, current_date_iso)

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """개인 경비 신청서 폼 데이터를 API Payload로 변환 (New Spec)"""
        logging.info("PersonalExpenseProcessor: Converting form data to API payload")

        payload = {
            "mstPid": "8",
            "aprvNm": form_data.get("title", "개인 경비 사용 신청"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get(
                "expense_reason", form_data.get("purpose", "개인 경비 사용 신청")
            ),
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

        # ---------------------
        # amountList 구성
        # ---------------------
        expenses_to_process = []

        # 1) expense_items 배열 우선 사용
        if form_data.get("expense_items"):
            expenses_to_process = form_data["expense_items"]
        # 2) HTML 개별 필드 fallback
        else:
            idx = 1
            while True:
                expense_date = form_data.get(f"expense_date_{idx}")
                expense_amount = form_data.get(f"expense_amount_{idx}")
                if not expense_date and not expense_amount:
                    break  # 더 이상 항목 없음
                expenses_to_process.append(
                    {
                        "expense_date": expense_date,
                        "expense_category": form_data.get(
                            f"expense_category_{idx}", ""
                        ),
                        "expense_description": form_data.get(
                            f"expense_description_{idx}", ""
                        ),
                        "expense_amount": expense_amount,
                        "expense_notes": form_data.get(f"expense_notes_{idx}", ""),
                    }
                )
                idx += 1

        category_mapping = {
            "traffic": "교통비",
            "accommodation": "숙박비",
            "meals": "식대",
            "entertainment": "접대비",
            "education": "교육훈련비",
            "supplies": "소모품비",
            "other": "기타",
        }

        invalid_dates = {None, "", "SLOT_NOT_FOUND_OR_UNDEFINED"}

        for expense in expenses_to_process:
            if expense.get("expense_date") in invalid_dates:
                # placeholder or empty row → 건너뜀
                continue
            dvNm = category_mapping.get(expense.get("expense_category", ""), "기타")
            # useRsn: description만 (notes는 aditInfo로 이동)
            desc = expense.get("expense_description", "")
            notes = expense.get("expense_notes", "")
            use_rsn = desc  # notes 제거
            adit_info = {"notes": notes} if notes and notes.strip() else {}

            payload["amountList"].append(
                {
                    "useYmd": expense.get("expense_date", ""),
                    "dvNm": dvNm,
                    "useRsn": use_rsn,
                    "qnty": 1,
                    "amt": (
                        int(expense.get("expense_amount", 0))
                        if str(expense.get("expense_amount", ""))
                        .replace(",", "")
                        .isdigit()
                        else 0
                    ),
                    "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                }
            )

        # ---------------------
        # 결재라인 추가
        # ---------------------
        if form_data.get("approvers"):
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
