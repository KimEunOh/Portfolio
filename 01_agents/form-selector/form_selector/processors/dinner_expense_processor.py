"""
야근 식대 신청서 전용 프로세서

야근 식대 신청서의 특화된 처리 로직:
- 자연어 시간 표현을 HH:MM 형식으로 변환
- 야근 관련 날짜 처리
- 식대 금액 및 계좌 정보 처리
"""

from typing import Dict, Any
from .base_processor import BaseFormProcessor
import logging
import json


class DinnerExpenseProcessor(BaseFormProcessor):
    """야근 식대 신청서 전용 프로세서"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """야근 식대 전처리"""
        processed_slots = slots.copy()

        # 퇴근 시간 변환 (자연어 → HH:MM 형식)
        if "overtime_time" in processed_slots:
            converted_time = self._convert_time_to_24h_format(
                processed_slots["overtime_time"]
            )
            if converted_time:
                processed_slots["overtime_time"] = converted_time

        return processed_slots

    def convert_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """야근 식대 관련 날짜 변환"""
        # 기본 날짜 변환 수행 (이미 application_date, work_date 등을 처리함)
        converted_slots = super().convert_dates(slots, current_date_iso)

        # 추가적인 야근 식대 특화 날짜 처리가 필요한 경우 여기에 추가
        # 현재는 기본 처리로 충분함

        return converted_slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """
        야근 식대는 아이템 리스트가 없으므로 기본 처리만 수행
        """
        return slots.copy()

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """야근 식대 아이템 날짜 변환

        야근 식대는 아이템이 없으므로 날짜 변환하지 않습니다.
        """
        logging.debug("DinnerExpenseProcessor: No item dates to convert")
        return slots

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """야근 식대 특화 필드 변환"""
        converted_slots = super().convert_fields(slots)

        # 숫자 필드 처리
        if "dinner_expense_amount" in converted_slots:
            try:
                # 문자열인 경우 숫자로 변환
                if isinstance(converted_slots["dinner_expense_amount"], str):
                    converted_slots["dinner_expense_amount"] = int(
                        converted_slots["dinner_expense_amount"]
                    )
            except (ValueError, TypeError):
                # 변환 실패 시 0으로 설정
                converted_slots["dinner_expense_amount"] = 0

        return converted_slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """야근 식대 후처리"""
        processed_slots = slots.copy()

        # 기본값 설정
        if "title" not in processed_slots or not processed_slots["title"]:
            processed_slots["title"] = "야근 식대 신청"

        if (
            "work_location" not in processed_slots
            or not processed_slots["work_location"]
        ):
            processed_slots["work_location"] = "회사"

        return processed_slots

    def _convert_time_to_24h_format(self, time_str: str) -> str:
        """
        자연어 시간 표현을 24시간 형식(HH:MM)으로 변환

        Args:
            time_str: 자연어 시간 표현 (예: "밤 10시 30분", "오후 9시")

        Returns:
            24시간 형식 시간 문자열 (예: "22:30", "21:00")
        """
        if not time_str or not isinstance(time_str, str):
            return ""

        import re

        time_str = time_str.strip()

        # 이미 HH:MM 형식인 경우 그대로 반환
        if re.match(r"^\d{1,2}:\d{2}$", time_str):
            return time_str

        # 시간과 분 추출을 위한 패턴들
        patterns = [
            # "밤 10시 30분", "저녁 8시 반"
            (
                r"(?:밤|저녁|야간)\s*(\d{1,2})시\s*(?:(\d{1,2})분|반)",
                lambda h, m: self._convert_evening_time(int(h), int(m) if m else 30),
            ),
            # "오후 9시", "오후 2시 15분"
            (
                r"오후\s*(\d{1,2})시\s*(?:(\d{1,2})분)?",
                lambda h, m: self._convert_pm_time(int(h), int(m) if m else 0),
            ),
            # "오전 1시", "새벽 2시 15분"
            (
                r"(?:오전|새벽)\s*(\d{1,2})시\s*(?:(\d{1,2})분)?",
                lambda h, m: self._convert_am_time(int(h), int(m) if m else 0),
            ),
            # "10시 30분", "9시"
            (
                r"(\d{1,2})시\s*(?:(\d{1,2})분|반)?",
                lambda h, m: self._convert_default_time(
                    int(h), int(m) if m else (30 if "반" in time_str else 0)
                ),
            ),
        ]

        for pattern, converter in patterns:
            match = re.search(pattern, time_str)
            if match:
                groups = match.groups()
                hour = groups[0]
                minute = groups[1] if len(groups) > 1 and groups[1] else None

                try:
                    result = converter(hour, minute)
                    if result:
                        return result
                except (ValueError, TypeError):
                    continue

        return ""  # 변환 실패

    def _convert_evening_time(self, hour: int, minute: int) -> str:
        """저녁/밤 시간을 24시간 형식으로 변환"""
        if hour <= 12:
            hour += 12  # 저녁/밤이므로 오후 시간으로 변환
        return f"{hour:02d}:{minute:02d}"

    def _convert_pm_time(self, hour: int, minute: int) -> str:
        """오후 시간을 24시간 형식으로 변환"""
        if hour != 12:
            hour += 12
        return f"{hour:02d}:{minute:02d}"

    def _convert_am_time(self, hour: int, minute: int) -> str:
        """오전/새벽 시간을 24시간 형식으로 변환"""
        if hour == 12:
            hour = 0  # 새벽 12시는 00시
        return f"{hour:02d}:{minute:02d}"

    def _convert_default_time(self, hour: int, minute: int) -> str:
        """기본 시간 변환 (문맥에 따라 오전/오후 판단)"""
        # 야근 시간이므로 8시 이후는 저녁으로 간주
        if hour >= 8:
            if hour <= 12:
                hour += 12  # 저녁 시간으로 변환
        else:
            # 1-7시는 새벽/오전으로 간주 (다음날 새벽)
            pass  # 그대로 유지

        return f"{hour:02d}:{minute:02d}"

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """야근 식대 신청서 폼 데이터를 API Payload로 변환 (Legacy 형식과 동일)"""
        logger.info("DinnerExpenseProcessor: Converting form data to API payload")

        # 기존 Legacy API 형식과 동일한 구조 사용
        payload = {
            "mstPid": "3",  # API 명세에 맞게 string 형태로 수정
            "aprvNm": form_data.get("title", "야근 식대 신청"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get(
                "work_details", form_data.get("notes", "야근 식대 신청")
            ),
            "apdInfo": json.dumps(
                {
                    "work_location": form_data.get("work_location", ""),
                    "overtime_time": form_data.get("overtime_time", ""),
                    "bank_account_for_deposit": form_data.get(
                        "bank_account_for_deposit", ""
                    ),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # amountList 구성 (비용 정산 정보)
        work_date = form_data.get("work_date", "")
        dinner_amount = form_data.get("dinner_expense_amount", 0)
        work_details = form_data.get("work_details", form_data.get("notes", ""))

        if work_date and dinner_amount:
            payload["amountList"].append(
                {
                    "useYmd": work_date,
                    "dvNm": "식대",
                    "useRsn": work_details,
                    "amount": int(dinner_amount) if dinner_amount else 0,
                }
            )

        # 결재라인 정보 추가 (Legacy와 동일하게 aprvPslId 사용)
        if "approvers" in form_data and form_data["approvers"]:
            for approver in form_data["approvers"]:
                payload["lineList"].append(
                    {
                        "aprvPslId": approver.aprvPsId,  # Legacy 형식: aprvPslId
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": approver.ordr,
                    }
                )

        logger.info("DinnerExpenseProcessor: API payload conversion completed")
        return payload
