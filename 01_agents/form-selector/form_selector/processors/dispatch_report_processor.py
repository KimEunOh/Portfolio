"""파견 및 출장보고서 전용 프로세서"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base_processor import BaseFormProcessor
import json
import logging


class DispatchReportProcessor(BaseFormProcessor):
    """파견 및 출장보고서 전용 프로세서

    - 날짜 범위 처리 (start_date, end_date)
    - 기간 계산 (duration_days)
    - 자연어 기간 표현 변환 ("2박 3일" → 3)
    - 단순한 필드 구조 (아이템 분해 없음)
    """

    # 자연어 기간 표현 매핑
    DURATION_PATTERNS = {
        r"(\d+)박\s*(\d+)일": lambda m: int(m.group(2)),  # "2박 3일" → 3
        r"(\d+)일간?": lambda m: int(m.group(1)),  # "5일간" → 5
        r"(\d+)일\s*동안": lambda m: int(m.group(1)),  # "3일 동안" → 3
        r"일주일": lambda m: 7,  # "일주일" → 7
        r"한\s*주": lambda m: 7,  # "한 주" → 7
        r"(\d+)주": lambda m: int(m.group(1)) * 7,  # "2주" → 14
        r"^(\d+)$": lambda m: int(m.group(1)),  # "10" → 10
    }

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """전처리: 기본값 설정"""
        processed = slots.copy()

        # 기본 제목 설정
        if not processed.get("title"):
            processed["title"] = "파견 및 출장 보고서"

        return processed

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """파견/출장 보고서 아이템 날짜 변환

        파견/출장 보고서는 아이템이 없으므로 날짜 변환하지 않습니다.
        """
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """아이템 처리: 파견 및 출장보고서는 아이템 분해가 없음"""
        # 파견 및 출장보고서는 복잡한 아이템 구조가 없으므로 그대로 반환
        return slots

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """필드 변환: duration_days 처리 및 기간 계산"""
        result = slots.copy()

        # duration_days 변환
        if "duration_days" in result and result["duration_days"]:
            # 자연어 표현을 숫자로 변환
            duration_str = str(result["duration_days"]).strip()
            converted_duration = self.convert_duration_days(duration_str)
            result["duration_days"] = converted_duration
        else:
            # duration_days가 없고 start_date, end_date가 있으면 계산
            if "start_date" in result and "end_date" in result:
                start_date = result.get("start_date")
                end_date = result.get("end_date")

                if start_date and end_date:
                    try:
                        # ISO 형식 날짜라면 기간 계산
                        if self._is_iso_date(start_date) and self._is_iso_date(
                            end_date
                        ):
                            start_dt = datetime.fromisoformat(start_date)
                            end_dt = datetime.fromisoformat(end_date)
                            duration = (end_dt - start_dt).days + 1  # 시작일 포함
                            result["duration_days"] = duration
                    except (ValueError, TypeError):
                        # 날짜 파싱 실패 시 기본값
                        pass

        return result

    def convert_duration_days(self, duration_str: str) -> int:
        """자연어 기간 표현을 숫자로 변환"""
        if not duration_str:
            return 0

        duration_str = duration_str.strip()

        # 패턴 매칭 시도
        for pattern, converter in self.DURATION_PATTERNS.items():
            match = re.search(pattern, duration_str)
            if match:
                return converter(match)

        # 매칭되지 않으면 숫자만 추출 시도
        numbers = re.findall(r"\d+", duration_str)
        if numbers:
            return int(numbers[0])

        # 그래도 안 되면 0
        return 0

    def _is_iso_date(self, date_str: str) -> bool:
        """ISO 날짜 형식인지 확인 (YYYY-MM-DD)"""
        if not date_str:
            return False

        pattern = r"^\d{4}-\d{2}-\d{2}$"
        return bool(re.match(pattern, date_str))

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """후처리: 빈 필드 기본값 설정"""
        processed = slots.copy()

        # 기본값 설정
        field_defaults = {
            "origin": "",
            "destination": "",
            "purpose": "",
            "report_details": "",
            "notes": "",
        }

        for field, default_value in field_defaults.items():
            if not processed.get(field):
                processed[field] = default_value

        return processed

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """파견/출장 보고서 폼 데이터를 API Payload로 변환"""
        logging.info("DispatchReportProcessor: Converting form data to API payload")

        payload = {
            "mstPid": "5",  # API 명세에 맞게 string 형태로 수정
            "aprvNm": form_data.get("title", "파견/출장 보고서"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("purpose", "파견/출장 보고서"),
            "apdInfo": json.dumps(
                {
                    "destination": form_data.get("destination", ""),
                    "period_days": int(form_data.get("duration_days", 0)),
                    "accomplishments": form_data.get("report_details", ""),
                    "notes": form_data.get("notes", ""),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # dayList 구성 (파견/출장 날짜 정보)
        start_date = form_data.get("start_date", "")
        end_date = form_data.get("end_date", "")

        if start_date and end_date:
            try:
                from datetime import datetime, timedelta

                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

                if start_dt <= end_dt:
                    current_date = start_dt
                    while current_date <= end_dt:
                        payload["dayList"].append(
                            {
                                "reqYmd": current_date.isoformat(),
                                "dvType": "DAY",
                            }
                        )
                        current_date += timedelta(days=1)
            except ValueError as e:
                logging.error(f"파견/출장 보고서 날짜 파싱 오류: {e}")

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

        logging.info("DispatchReportProcessor: API payload conversion completed")
        return payload
