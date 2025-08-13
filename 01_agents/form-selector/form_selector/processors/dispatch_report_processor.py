"""파견 및 출장보고서 전용 프로세서"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base_processor import BaseFormProcessor
import json
import logging
from ..utils import parse_relative_date_to_iso


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

        if "origin" not in processed or not processed["origin"]:
            processed["origin"] = "사무실"

        return processed

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """아이템 처리: 파견 및 출장보고서는 아이템 분해가 없음"""
        # 파견 및 출장보고서는 복잡한 아이템 구조가 없으므로 그대로 반환
        return slots

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
        """파견 및 출장 보고서 후처리"""
        return slots

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """파견 및 출장 보고서 폼 데이터를 API Payload로 변환"""
        logging.info("DispatchReportProcessor: Converting form data to API payload")

        # drafterId: snake/camel 모두 수용
        drafter_id = form_data.get("drafter_id") or form_data.get("drafterId") or ""

        # 총 일수(periodDays) 계산: 우선 duration_days/durationDays 사용, 없으면 날짜 차이로 계산(포함일 기준)
        start_date = form_data.get("start_date", "")
        end_date = form_data.get("end_date", "")
        duration_raw = (
            form_data.get("duration_days")
            or form_data.get("durationDays")
            or form_data.get("duration")
        )
        period_days = 0
        try:
            if duration_raw is not None and str(duration_raw).strip() != "":
                try:
                    period_days = int(duration_raw)
                except ValueError:
                    period_days = self.convert_duration_days(str(duration_raw))
        except Exception:
            period_days = 0

        # duration 정보가 없으면 날짜 차이로 포함일 계산
        if period_days <= 0 and start_date and end_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d").date()
                ed = datetime.strptime(end_date, "%Y-%m-%d").date()
                if sd <= ed:
                    period_days = (ed - sd).days + 1
            except Exception:
                period_days = 0

        # 보고/비고 플레이스홀더 방지: 템플릿 플레이스홀더가 그대로 전달된 경우 빈 문자열로 정리
        def clean_placeholder(val: Optional[str]) -> str:
            if not val:
                return ""
            try:
                s = str(val)
                if s.startswith("{") and s.endswith("}"):
                    return ""
                if "SLOT_NOT_FOUND" in s:
                    return ""
                return s
            except Exception:
                return ""

        payload = {
            "mstPid": "5",  # API 명세에 맞게 string 형태로 수정
            "aprvNm": "파견 및 출장 보고서",
            "drafterId": drafter_id,
            "docCn": clean_placeholder(form_data.get("purpose", "파견/출장 보고서")),
            "apdInfo": json.dumps(
                {
                    "destination": form_data.get("destination", ""),
                    "periodDays": int(period_days),
                    "reportDetails": clean_placeholder(
                        form_data.get("report_details", "")
                    ),
                    "notes": clean_placeholder(form_data.get("notes", "")),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # dayList 구성 (파견/출장 날짜 정보)

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
                        "aprvPsId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        # 안전장치: periodDays가 0일 때 dayList 길이로 보정
        try:
            apd = json.loads(payload.get("apdInfo", "{}"))
            cur_days = int(apd.get("periodDays", 0) or 0)
            if cur_days <= 0 and payload.get("dayList"):
                apd["periodDays"] = len(payload["dayList"])
                payload["apdInfo"] = json.dumps(apd, ensure_ascii=False)
        except Exception:
            pass

        logging.info("DispatchReportProcessor: API payload conversion completed")
        return payload
