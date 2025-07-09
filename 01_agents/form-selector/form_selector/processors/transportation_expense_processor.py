"""
교통비 신청서 전용 프로세서
"""

from typing import Dict, Any
from .base_processor import BaseFormProcessor
import logging
import json


class TransportationExpenseProcessor(BaseFormProcessor):
    """
    교통비 신청서 데이터 처리.
    - 슬롯 추출 후 템플릿 채우기 (기존 로직)
    - 프론트엔드 form 제출 데이터 API 페이로드로 변환 (신규 로직)
    """

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)

    # --- 슬롯 처리 관련 메소드들 (템플릿 채우기용) ---

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        processed_slots = slots.copy()
        if "title" not in processed_slots or not processed_slots["title"]:
            processed_slots["title"] = "교통비 신청"
        return processed_slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        return slots.copy()

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        processed_slots = slots.copy()
        if "purpose" not in processed_slots or not processed_slots["purpose"]:
            processed_slots["purpose"] = "업무 관련 교통비"
        return processed_slots

    # --- Form 데이터 API 변환 메소드 ---

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        교통비 신청서 HTML 폼 데이터를 API 페이로드로 변환합니다.
        amountList의 각 항목을 API 명세에 맞는 구조로 매핑합니다.
        """
        purpose = form_data.get("purpose", "")
        notes = form_data.get("notes", "")
        amount_list = form_data.get("amountList", [])

        # 1) amountList 변환
        converted_amount_list = []
        earliest_date = None
        first_origin = ""
        first_destination = ""
        for idx, item in enumerate(amount_list):
            transport_type = item.get("transportType", "other")
            origin = item.get("origin", "")
            destination = item.get("destination", "")
            boarding_date = item.get("boardingDate", "")  # YYYY-MM-DD
            amount = int(item.get("amount", 0))

            if idx == 0:
                first_origin = origin
                first_destination = destination
            # Earliest boarding date 계산
            if boarding_date:
                if earliest_date is None or boarding_date < earliest_date:
                    earliest_date = boarding_date

            converted_amount_list.append(
                {
                    "useYmd": boarding_date,
                    "dvNm": self._map_transport_type(transport_type),
                    "useRsn": f"{origin} -> {destination}",
                    "amt": amount,
                    "aditInfo": json.dumps({}, ensure_ascii=False),
                }
            )

        # 2) dayList (가장 빠른 탑승일 기준)
        day_list = []

        # 3) apdInfo (출발/도착/비고 정보 JSON 문자열)
        apd_info_obj = {
            "origin": first_origin,
            "destination": first_destination,
            "notes": notes,
        }

        payload = {
            "mstPid": "4",
            "aprvNm": form_data.get("title", "교통비 신청서"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": purpose or notes,
            "apdInfo": json.dumps(apd_info_obj, ensure_ascii=False),
            "lineList": [],
            "dayList": [],
            "amountList": converted_amount_list,
        }

        # 4) lineList (approvers)
        approvers = form_data.get("approvers", [])
        for approver in approvers:
            try:
                aprv_id = getattr(approver, "aprvPsId", None) or approver.get(
                    "aprvPsId"
                )
                payload["lineList"].append(
                    {
                        "aprvPslId": aprv_id,
                        "aprvDvTy": getattr(approver, "aprvDvTy", None)
                        or approver.get("aprvDvTy"),
                        "ordr": getattr(approver, "ordr", None)
                        or approver.get("ordr", 0),
                    }
                )
            except Exception:
                continue

        return payload

    def _map_transport_type(self, transport_type_en: str) -> str:
        """영문 교통수단 타입을 한글 코드로 변환합니다."""
        mapping = {
            "subway": "지하철",
            "bus": "버스",
            "train": "기차",
            "airplane": "항공",
            "other": "기타",
        }
        return mapping.get(transport_type_en, "기타")
