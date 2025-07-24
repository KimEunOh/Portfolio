"""
교통비 신청서 전용 프로세서

교통비 신청서의 특화된 처리 로직:
- 출발지/목적지 처리
- 교통비 금액 변환 (문자열 → 숫자)
- 출발일 날짜 처리
- 교통 내역 상세 처리
"""

from typing import Dict, Any
from .base_processor import BaseFormProcessor
import logging
import json
from ..utils import parse_relative_date_to_iso


class TransportationExpenseProcessor(BaseFormProcessor):
    """교통비 신청서 전용 프로세서"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """교통비 전처리"""
        processed_slots = slots.copy()

        # total_amount 키 보존 - BaseFormProcessor의 None 필터링으로 키가 제거된 경우에도 처리
        if "total_amount" not in processed_slots:
            # None 값으로 인해 키가 제거된 경우
            processed_slots["total_amount"] = 0
        elif processed_slots["total_amount"] == "":  # 빈 문자열 처리
            processed_slots["total_amount"] = 0

        return processed_slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        교통비 아이템 리스트의 각 항목을 처리합니다.
        - 각 아이템의 'amount'를 정수로 변환합니다.
        - 'items' 키가 없거나 비어있으면 빈 리스트를 추가합니다.
        """
        converted_slots = slots.copy()
        items = converted_slots.get("items", [])

        if not items:
            converted_slots["items"] = []
            return converted_slots

        processed_items = []
        for item in items:
            processed_item = item.copy()
            processed_item["amount"] = self._convert_amount_to_int(
                processed_item.get("amount")
            )
            processed_items.append(processed_item)

        converted_slots["items"] = processed_items
        return converted_slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """교통비 후처리: 아이템 금액을 합산하여 total_amount 업데이트"""
        processed_slots = slots.copy()

        # items 리스트의 amount를 합산하여 total_amount 계산
        if "items" in processed_slots and isinstance(processed_slots["items"], list):
            total_amount = sum(
                item.get("amount", 0) for item in processed_slots["items"]
            )
            processed_slots["total_amount"] = total_amount
            logging.info(
                f"TransportationExpenseProcessor: Calculated total_amount: {total_amount}"
            )

        return processed_slots

    def _convert_amount_to_int(self, amount_value: Any) -> int:
        """
        금액 값을 정수로 변환

        Args:
            amount_value: 금액 값 (문자열, 숫자, None 등)

        Returns:
            정수 금액 (변환 실패 시 0)
        """
        if amount_value is None:
            return 0

        if isinstance(amount_value, int):
            return amount_value

        if isinstance(amount_value, float):
            return int(amount_value)

        if isinstance(amount_value, str):
            amount_value = amount_value.strip()
            if not amount_value:
                return 0

            try:
                # 숫자가 아닌 문자 제거 (쉼표, 원 등)
                import re

                clean_amount = re.sub(r"[^\d.]", "", amount_value)
                if clean_amount:
                    return int(float(clean_amount))
                else:
                    return 0
            except (ValueError, TypeError):
                return 0

        return 0

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """교통비 신청서 폼 데이터를 API Payload로 변환 (New Spec)"""

        # purpose 필드가 비어있으면 기본 제목 설정
        doc_title = form_data.get("purpose") or "교통비 신청"

        payload = {
            "mstPid": "4",
            "aprvNm": doc_title,
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("purpose", "교통비 신청"),
            "apdInfo": json.dumps(
                {
                    "items": form_data.get("items", []),
                    "notes": form_data.get("notes", ""),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # amountList 구성: 각 교통 내역 아이템을 별도의 항목으로 추가
        departure_date = form_data.get("departure_date", "")
        items = form_data.get("items", [])
        purpose = form_data.get("purpose", "")

        for item in items:
            # useRsn: 목적(용무)를 기본으로, 아이템별 비고가 있으면 함께 표시
            reason_parts = [purpose]
            if item.get("notes"):
                reason_parts.append(item["notes"])
            use_reason = " - ".join(filter(None, reason_parts))

            # dvNm: 교통수단을 기본으로, 출발지/목적지 정보 추가
            dvnm_parts = [item.get("transport_type", "기타")]
            if item.get("origin") or item.get("destination"):
                dvnm_parts.append(
                    f"({item.get('origin', '')} → {item.get('destination', '')})"
                )
            dv_name = " ".join(filter(None, dvnm_parts))

            payload["amountList"].append(
                {
                    "useYmd": departure_date,
                    "dvNm": dv_name,
                    "useRsn": use_reason,
                    "qnty": 1,
                    "amt": item.get("amount", 0),
                    "aditInfo": json.dumps(item, ensure_ascii=False),
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
        return payload
