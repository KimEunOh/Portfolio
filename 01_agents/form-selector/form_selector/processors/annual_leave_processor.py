"""
연차 신청서 전용 처리기

연차 신청서의 특별한 처리 로직을 담당합니다.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime, timedelta
import re

from .base_processor import BaseFormProcessor
from ..utils import parse_duration_to_days  # 새로운 유틸리티 함수 임포트


class AnnualLeaveProcessor(BaseFormProcessor):
    """연차 신청서 전용 처리기"""

    def __init__(self, form_config: Dict[str, Any] = None):
        super().__init__(form_config)
        logging.info("AnnualLeaveProcessor initialized")

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """연차 신청서 전처리

        연차 신청서는 특별한 전처리가 필요하지 않습니다.
        """
        logging.debug("AnnualLeaveProcessor: No special preprocessing needed")
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """연차 신청서 아이템 변환

        연차 신청서는 아이템 리스트가 없으므로 변환하지 않습니다.
        """
        logging.debug("AnnualLeaveProcessor: No items to convert")
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """연차 신청서 후처리
        - end_date 또는 duration에 기간이 명시된 경우, 이를 leave_days로 변환합니다.
        - 시작일과 leave_days를 기반으로 종료일을 계산합니다.
        """
        # 1. 기간 정보가 다른 슬롯에 잘못 들어갔는지 확인하고 leave_days로 이동
        duration_source_slots = ["end_date", "duration", "leave_days"]
        parsed_days = None

        if not slots.get("leave_days"):  # leave_days가 비어있을 때만 시도
            for slot_name in duration_source_slots:
                source_value = slots.get(slot_name)
                if isinstance(source_value, str):
                    days = parse_duration_to_days(source_value)
                    if days is not None:
                        parsed_days = days
                        slots["leave_days"] = parsed_days
                        logging.info(
                            f"Moved duration from '{slot_name}' ({source_value}) to 'leave_days' ({parsed_days} days)."
                        )
                        # 기간을 찾았으면, 원래 슬롯은 비워주어 혼동을 방지
                        if slot_name == "end_date":
                            slots["end_date"] = None
                        break  # 첫 번째로 찾은 기간 정보를 사용

        # 2. 시작일과 기간(leave_days)으로 종료일 계산
        start_date_str = slots.get("start_date")
        leave_days = slots.get("leave_days")
        end_date_str = slots.get("end_date")

        # 종료일이 없거나, 유효한 날짜 형식이 아닐 때만 계산 시도
        is_end_date_invalid = not end_date_str or not re.match(
            r"\d{4}-\d{2}-\d{2}", str(end_date_str)
        )

        if start_date_str and leave_days and is_end_date_invalid:
            try:
                # leave_days가 "3"과 같이 문자열일 수 있으므로 float으로 변환
                days_to_add = float(leave_days)
                # '3일간'은 시작일 포함 3일이므로 (3 - 1)일을 더해야 함
                # 반차(0.5) 등 1일 미만은 날짜를 더하지 않음
                delta = days_to_add - 1 if days_to_add >= 1 else 0

                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = start_date + timedelta(days=int(delta))
                slots["end_date"] = end_date.isoformat()
                logging.info(
                    f"Calculated end_date: {slots['end_date']} from start_date: {start_date_str} and leave_days: {leave_days}"
                )
            except (ValueError, TypeError) as e:
                logging.warning(
                    f"Could not calculate end_date from start_date='{start_date_str}' and leave_days='{leave_days}'. Error: {e}"
                )

        # 3. 시작일과 종료일이 있는데 연차일수가 없으면 역으로 계산
        start_date_str = slots.get("start_date")
        end_date_str = slots.get("end_date")
        leave_days = slots.get("leave_days")

        if (
            start_date_str
            and end_date_str
            and not leave_days
            and re.match(r"\d{4}-\d{2}-\d{2}", str(start_date_str))
            and re.match(r"\d{4}-\d{2}-\d{2}", str(end_date_str))
        ):
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                if end_date >= start_date:
                    calculated_days = (end_date - start_date).days + 1
                    slots["leave_days"] = float(calculated_days)
                    logging.info(
                        f"Calculated leave_days: {slots['leave_days']} from start_date: {start_date_str} and end_date: {end_date_str}"
                    )
            except (ValueError, TypeError) as e:
                logging.warning(
                    f"Could not calculate leave_days from start_date='{start_date_str}' and end_date='{end_date_str}'. Error: {e}"
                )

        return slots

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """연차 신청서 아이템 날짜 변환

        연차 신청서는 아이템이 없으므로 날짜 변환하지 않습니다.
        """
        logging.debug("AnnualLeaveProcessor: No item dates to convert")
        return slots

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """연차 신청서 폼 데이터를 API Payload로 변환 (Legacy 형식과 동일)"""
        logger.info("AnnualLeaveProcessor: Converting form data to API payload")

        # 기존 Legacy API 형식과 동일한 구조 사용
        payload = {
            "mstPid": "1",  # API 명세에 맞게 string 형태로 수정
            "aprvNm": form_data.get("title", "연차 사용 신청"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": form_data.get("reason", "개인 사유"),
            "apdInfo": json.dumps({}, ensure_ascii=False),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # dayList 구성 (연차 날짜 정보) - 날짜 범위 전체 생성
        start_date = form_data.get("start_date", "")
        end_date = form_data.get("end_date", "")
        leave_type = form_data.get("leave_type", "annual")

        # 휴가 종류를 API dvType으로 변환
        dv_type_map = {
            "annual": "DAY",
            "half_day_morning": "HALF_AM",
            "half_day_afternoon": "HALF_PM",
            "quarter_day_morning": "QUARTER_AM",
            "quarter_day_afternoon": "QUARTER_PM",
        }

        if start_date and end_date:
            try:
                # 날짜 문자열을 datetime 객체로 변환
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

                logging.info(
                    f"[연차 신청서] dayList 생성 시작: {start_date} ~ {end_date}"
                )

                if start_dt <= end_dt:
                    current_date = start_dt
                    while current_date <= end_dt:
                        payload["dayList"].append(
                            {
                                "reqYmd": current_date.isoformat(),  # YYYY-MM-DD 형식
                                "dvType": dv_type_map.get(leave_type, "DAY"),
                            }
                        )
                        current_date += timedelta(days=1)

                    logging.info(
                        f"[연차 신청서] dayList 생성 완료: {len(payload['dayList'])}개 날짜"
                    )
                else:
                    logging.warning(
                        f"[연차 신청서] 잘못된 날짜 순서: start_date({start_date}) > end_date({end_date})"
                    )

            except ValueError as e:
                logging.error(
                    f"[연차 신청서] 날짜 파싱 오류: {e}, start_date={start_date}, end_date={end_date}"
                )
            except Exception as e:
                logging.error(f"[연차 신청서] dayList 생성 중 예외 발생: {e}")
        elif start_date:
            # end_date가 없고 start_date만 있는 경우 (당일 휴가)
            payload["dayList"].append(
                {"reqYmd": start_date, "dvType": dv_type_map.get(leave_type, "DAY")}
            )
            logging.info(f"[연차 신청서] 당일 휴가 dayList 생성: {start_date}")
        else:
            logging.warning(
                f"[연차 신청서] 시작일이 누락되어 dayList를 생성할 수 없습니다."
            )

        # 결재라인 정보 추가 (Legacy와 동일하게 aprvPslId 사용)
        if "approvers" in form_data and form_data["approvers"]:
            for approver in form_data["approvers"]:
                payload["lineList"].append(
                    {
                        "aprvPslId": approver.aprvPsId,  # Legacy 형식: aprvPslId
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("AnnualLeaveProcessor: API payload conversion completed")
        return payload
