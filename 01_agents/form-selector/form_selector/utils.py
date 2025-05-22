from datetime import datetime, timedelta
from dateutil.parser import parse, ParserError
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
import re  # 정규표현식 모듈 임포트
from typing import Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field

from .llm import llm  # llm.py 에서 공유 LLM 객체 가져오기
from langchain_core.messages import HumanMessage, AIMessage


# Function calling을 위한 함수 스키마 정의
class DateTimeOutput(BaseModel):
    """날짜/시간 정보 추출 결과"""

    date_time: Optional[str] = Field(
        description="추출된 날짜/시간 정보. YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM 형식으로 표현. 추출할 수 없는 경우 null."
    )
    date_only: bool = Field(
        description="시간 정보가 없이 날짜 정보만 있는 경우 true, 시간 정보도 있으면 false"
    )


# LLM 기반 날짜/시간 파싱을 위한 함수
def _call_llm_for_datetime_parsing(text: str, today_iso: str) -> Optional[str]:
    """
    주어진 텍스트에서 날짜 또는 날짜시간 정보를 LLM을 통해 파싱합니다.
    Function calling을 활용하여 결과를 구조화된 형태로 받습니다.

    성공 시 "YYYY-MM-DD" 또는 "YYYY-MM-DDTHH:MM" 형식의 문자열을 반환하고,
    실패 시 None을 반환합니다.

    Args:
        text: 파싱할 원본 사용자 입력 문자열 (예: "다음 주 화요일 오후 3시 반")
        today_iso: LLM에게 컨텍스트로 제공할 오늘 날짜 (YYYY-MM-DD 형식)

    Returns:
        파싱된 날짜/날짜시간 문자열 또는 None
    """
    # 1. 프롬프트 구성
    prompt = f"""
오늘 날짜는 {today_iso}입니다.
사용자 입력 텍스트는 "{text}" 입니다.

이 텍스트에서 날짜 또는 날짜와 시간 정보를 추출하세요.
만약 텍스트에서 유효한 날짜나 시간 정보를 명확히 추출할 수 없거나, 정보가 부족하여 정확한 변환이 불가능하다면, date_time을 null로 설정하세요.

예를 들어:
- 입력이 "내일 회의"라면 시간 정보가 없으므로 date_time="{(datetime.fromisoformat(today_iso) + timedelta(days=1)).strftime('%Y-%m-%d')}", date_only=true
- 입력이 "내일 오후 3시"라면 date_time="{(datetime.fromisoformat(today_iso) + timedelta(days=1)).strftime('%Y-%m-%d')}T15:00", date_only=false
- 입력이 "회의" 라거나 의미없는 문자열이라면 date_time=null, date_only=true
"""

    # 2. Function calling 설정
    functions = [
        {
            "name": "extract_date_time",
            "description": "텍스트에서 날짜와 시간 정보를 추출합니다",
            "parameters": DateTimeOutput.model_json_schema(),
        }
    ]

    try:
        # 3. LLM 호출
        model_with_functions = llm.bind(functions=functions)
        response = model_with_functions.invoke(prompt)

        # 4. Function calling 응답 처리
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Function calling 응답이 있는 경우
            tool_call = response.tool_calls[0]
            if tool_call.get("name") == "extract_date_time":
                try:
                    args = tool_call.get("args", {})
                    date_time = args.get("date_time")

                    # date_time이 None이면 파싱 실패로 처리
                    if date_time is None:
                        return None

                    # 날짜 또는 날짜+시간 형식 검증
                    is_date_format = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_time))
                    is_datetime_format = bool(
                        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", date_time)
                    )

                    if is_date_format or is_datetime_format:
                        try:
                            if is_datetime_format:
                                datetime.strptime(date_time, "%Y-%m-%dT%H:%M")
                            else:  # is_date_format
                                datetime.strptime(date_time, "%Y-%m-%d")
                            return date_time
                        except ValueError:
                            return None
                    return None
                except Exception as e:
                    print(f"Function calling 응답 처리 중 오류 (utils.py): {e}")
                    return None

        # Function calling 응답이 없거나 처리 실패 시 일반 응답 처리
        if hasattr(response, "content") and isinstance(response.content, str):
            content = response.content.strip()

            # 응답에서 ISO 날짜/시간 패턴 추출 시도
            date_pattern = r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?"
            date_matches = re.findall(date_pattern, content)

            if date_matches:
                date_str = date_matches[0]  # 첫 번째 매치 사용

                # 형식 검증
                is_date_format = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str))
                is_datetime_format = bool(
                    re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", date_str)
                )

                if is_date_format or is_datetime_format:
                    try:
                        if is_datetime_format:
                            datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
                        else:  # is_date_format
                            datetime.strptime(date_str, "%Y-%m-%d")
                        return date_str
                    except ValueError:
                        return None

            # "None" 문자열 처리
            if content.lower() == "none":
                return None

        return None

    except Exception as e:
        print(f"LLM API 호출 중 오류 (utils.py): {e}")
        return None


# 한국어 요일 -> dateutil 요일 객체 매핑
DAY_MAP = {
    "월요일": MO,
    "월": MO,
    "화요일": TU,
    "화": TU,
    "수요일": WE,
    "수": WE,
    "목요일": TH,
    "목": TH,
    "금요일": FR,
    "금": FR,
    "토요일": SA,
    "토": SA,
    "일요일": SU,
    "일": SU,
}


def preprocess_date_str(date_str: str, today: datetime.date) -> str:
    """특정 날짜 형식 전처리 및 시간 표현 제거"""
    processed_str = date_str
    # "YYYY년 MM월 DD일" / "YYYY년M월D일" -> "YYYY-MM-DD"
    processed_str = re.sub(
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}",
        processed_str,
    )
    # "MM월 DD일" / "M월D일" -> "{this_year}-MM-DD"
    # YYYY-MM-DD 형식으로 이미 바뀐 경우는 건드리지 않도록 조건 추가 필요 (간단히 처리)
    if not re.match(r"\d{4}-\d{1,2}-\d{1,2}", processed_str):
        processed_str = re.sub(
            r"(\d{1,2})월\s*(\d{1,2})일",
            lambda m: f"{today.year}-{m.group(1)}-{m.group(2)}",
            processed_str,
        )

    # "다음 주", "이번 주" 등의 키워드가 포함된 경우 시간 정보만 제거 시도
    week_keywords = [
        "다음주",
        "차주",
        "지난주",
        "전주",
        "금주",
        "이번주",
        "다음 주",
        "이번 주",
        "지난 주",
    ]
    contains_week_keyword = any(
        wk_keyword in processed_str for wk_keyword in week_keywords
    )

    time_related_patterns = (
        r"(오전|오후|아침|저녁|밤|새벽|\d{1,2}시(\s*\d{1,2}분)?(\s*\d{1,2}초)?)"
    )
    processed_str = re.sub(time_related_patterns, "", processed_str).strip()

    # "다음 주 월요일" 같은 구문은 유지하고, "내일 아침" -> "내일"로 변경
    if not contains_week_keyword:
        parts = processed_str.split()
        if parts:
            # "오늘", "내일" 등 단일 키워드 뒤에 불필요한 숫자 등이 붙는 경우 제거
            # 예: "내일 10" (10시가 제거된 후) -> "내일"
            if (
                parts[0].lower()
                in ["오늘", "내일", "어제", "모레", "그저께", "금일", "명일", "작일"]
                and len(parts) > 1
            ):
                processed_str = parts[0]
            elif len(parts) > 0:  # 그 외 일반적인 경우 첫 어절 사용
                processed_str = parts[0]
            # else: parts가 비어있으면 processed_str 그대로 유지 (위에서 strip() 했으므로 거의 발생 안함)

    return processed_str.strip()  # 최종적으로 양끝 공백 제거


def parse_relative_date_to_iso(date_str: str) -> str:
    """다양한 상대적/절대적 날짜 표현을 YYYY-MM-DD 형식으로 변환합니다.
    변환 실패 시 원본 문자열을 반환합니다.
    """
    if not isinstance(date_str, str):
        return date_str

    today = datetime.now().date()
    original_date_str = date_str.strip()

    # 전처리 단계 추가
    processed_for_keyword_and_parse = preprocess_date_str(original_date_str, today)

    # 상대 날짜 키워드용 전처리 (공백제거, 소문자화)
    relative_keyword_str = processed_for_keyword_and_parse.lower().replace(" ", "")

    try:
        dt = None
        if relative_keyword_str in ["오늘", "금일"]:
            dt = today
        elif relative_keyword_str in ["내일", "명일"]:
            dt = today + timedelta(days=1)
        elif relative_keyword_str in ["어제", "작일"]:
            dt = today - timedelta(days=1)
        elif relative_keyword_str == "모레":
            dt = today + timedelta(days=2)
        elif relative_keyword_str in ["그저께", "그끄제"]:
            dt = today - timedelta(days=2)
        else:
            # "다음주/차주/지난주/전주/이번주 [요일]" 패턴 처리
            match = re.match(
                r"(다음주|차주|지난주|전주|금주|이번주)([월화수목금토일])(요일)?",  # 요일 뒤 '요일'은 선택사항
                relative_keyword_str,
            )
            if match:
                week_prefix = match.group(1)
                day_char = match.group(2)  # 예: "월", "화"
                # day_suffix = match.group(3) # "요일" 또는 None

                day_name_key = day_char  # DAY_MAP 검색용 키 (예: "월")
                if day_name_key in DAY_MAP:  # DAY_MAP에 "월", "화" 등이 키로 있어야 함
                    target_weekday_obj = DAY_MAP[day_name_key]
                    this_week_monday = today - timedelta(days=today.weekday())

                    if week_prefix in ["다음주", "차주"]:
                        next_week_monday = this_week_monday + timedelta(weeks=1)
                        dt = next_week_monday + relativedelta(
                            weekday=target_weekday_obj(0)
                        )
                    elif week_prefix in ["지난주", "전주"]:
                        last_week_monday = this_week_monday - timedelta(weeks=1)
                        dt = last_week_monday + relativedelta(
                            weekday=target_weekday_obj(0)
                        )
                    elif week_prefix in ["금주", "이번주"]:
                        dt = this_week_monday + relativedelta(
                            weekday=target_weekday_obj(0)
                        )
            elif relative_keyword_str in DAY_MAP:  # 예: "금요일", "월"
                target_weekday_obj = DAY_MAP[relative_keyword_str]
                days_ahead = (target_weekday_obj.weekday - today.weekday() + 7) % 7
                dt = today + timedelta(days=days_ahead)

            if dt is None:  # 매칭되지 않거나, 위 로직에서 dt가 설정 안된 경우
                # 전처리된 문자열(processed_for_keyword_and_parse)로 일반 파싱 시도
                dt = parse(processed_for_keyword_and_parse).date()

        if dt:
            return dt.isoformat()
        else:
            return original_date_str

    except (ParserError, ValueError):  # 일반 파싱 실패 시
        # 기존 로직 실패 시 LLM 호출 시도
        llm_result = _call_llm_for_datetime_parsing(
            original_date_str, datetime.now().date().isoformat()
        )
        if llm_result and re.match(r"^\d{4}-\d{2}-\d{2}", llm_result):
            return llm_result
        return original_date_str
    except Exception:  # 기타 예외
        # 기타 예외 발생 시 LLM 호출 시도
        llm_result = _call_llm_for_datetime_parsing(
            original_date_str, datetime.now().date().isoformat()
        )
        if llm_result and re.match(r"^\d{4}-\d{2}-\d{2}", llm_result):
            return llm_result
        return original_date_str


def parse_datetime_description_to_iso_local(datetime_str: str) -> Optional[str]:
    """ "오늘 오후 3시", "내일 10시 반" 같은 문자열을 "YYYY-MM-DDTHH:MM"으로 변환"""
    if not isinstance(datetime_str, str):
        # 입력 타입이 문자열이 아니면 LLM 호출 없이 바로 반환 (또는 None)
        # 이 경우는 보통 오류 상황이므로, LLM에 넘기기보다 빠르게 실패 처리
        return datetime_str  # 또는 None으로 통일할 수 있음

    original_datetime_str = datetime_str.strip()
    original_datetime_str_lower = original_datetime_str.lower()  # 소문자 변환 추가
    today_obj = datetime.now()  # LLM에 전달할 오늘 날짜를 위해 datetime 객체 사용
    today_iso_for_llm = today_obj.date().isoformat()

    # --- '정오', '자정' 특별 처리 로직 시작 ---
    hour, minute = 0, 0
    explicit_time_set = False
    date_part_str_for_special_keywords = original_datetime_str  # 원본에서 키워드 제거용

    # "정오" 또는 "자정"이 포함되어 있는지 확인
    # 단순 문자열 포함으로 확인하므로 "정오각형" 같은 단어는 걸러내지 못할 수 있음.
    # 더 정확하려면 정규식으로 단어 경계를 확인하거나, 전처리된 문자열 사용.
    # 여기서는 우선 단순 포함으로 처리하고, 문제가 되면 개선.

    # `replace`를 사용할 때, 중복 키워드(예: "자정 자정")는 첫 번째만 처리됨.
    # 여러 번 등장하는 경우가 일반적이지 않으므로 일단 이대로 둠.
    if "정오" in original_datetime_str_lower:
        hour, minute = 12, 0
        explicit_time_set = True
        # "정오" 문자열 제거 (대소문자 무시하고 첫번째 것만)
        # re.sub를 사용하여 대소문자 구분 없이 제거
        date_part_str_for_special_keywords = re.sub(
            r"정오", "", original_datetime_str, flags=re.IGNORECASE, count=1
        ).strip()
        if not date_part_str_for_special_keywords:
            date_part_str_for_special_keywords = "오늘"

    elif "자정" in original_datetime_str_lower:
        hour, minute = 0, 0
        explicit_time_set = True
        date_part_str_for_special_keywords = re.sub(
            r"자정", "", original_datetime_str, flags=re.IGNORECASE, count=1
        ).strip()
        if not date_part_str_for_special_keywords:
            date_part_str_for_special_keywords = "오늘"
        # "내일 자정"의 경우, `date_part_str_for_special_keywords`가 "내일"이 되고,
        # `parse_relative_date_to_iso("내일")`이 날짜를 처리.

    if explicit_time_set:
        iso_date_str = parse_relative_date_to_iso(date_part_str_for_special_keywords)
        if not iso_date_str or not re.match(r"\d{4}-\d{2}-\d{2}", iso_date_str):
            # 날짜 부분 해석 불가시 LLM 시도
            llm_result = _call_llm_for_datetime_parsing(
                original_datetime_str, today_iso_for_llm
            )
            return llm_result
        try:
            final_dt_obj = datetime.strptime(iso_date_str, "%Y-%m-%d").replace(
                hour=hour, minute=minute
            )
            return final_dt_obj.strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            llm_result = _call_llm_for_datetime_parsing(
                original_datetime_str, today_iso_for_llm
            )
            return llm_result
    # --- '정오', '자정' 특별 처리 로직 끝 ---

    # 1. 날짜 부분 추출 시도 (간단한 키워드 우선)
    date_part_str = original_datetime_str
    time_part_str = ""  # 시간 부분을 담을 변수

    # 시간 관련 키워드 및 패턴 정의 (예: HH:MM, HH시 MM분, 오전/오후 등)
    # 정규표현식으로 시간 부분을 먼저 분리 시도
    # 예: "오늘 오후 3시 반", "내일 10:30", "모레 2시"
    # 좀 더 정교한 시간 패턴 매칭이 필요할 수 있음
    time_pattern = re.compile(
        r"(?:(오전|오후|아침|저녁|밤|새벽|정오|자정|낮)\s*)?"
        + r"(\d{1,2})\s*시(?:\s*(\d{1,2}|반|정각)\s*분?)?"
        + r"(?:\s*(\d{1,2})\s*초)?"
    )
    time_match = time_pattern.search(original_datetime_str)

    hour, minute = 0, 0  # 기본값

    if time_match:
        time_part_extracted = time_match.group(0)
        date_part_str = original_datetime_str.replace(time_part_extracted, "").strip()
        if not date_part_str:  # 시간만 입력된 경우 (예: "오후 3시") 오늘 날짜 사용
            date_part_str = "오늘"

        am_pm_group = time_match.group(1)
        hour_group = time_match.group(2)
        minute_group = time_match.group(3)
        # second_group = time_match.group(4) # 초는 현재 미사용

        if hour_group:
            hour = int(hour_group)

        if am_pm_group:
            if am_pm_group in ["오후", "저녁", "밤"] and hour < 12:
                hour += 12
            elif am_pm_group == "오전" and hour == 12:  # 오전 12시 -> 00시
                hour = 0
            elif (
                am_pm_group == "자정"
            ):  # time_pattern에 의해 "자정"이 am_pm_group으로 잡히는 경우는 거의 없으나 방어적으로 추가
                hour = 0
            elif (
                am_pm_group == "정오"
            ):  # time_pattern에 의해 "정오"가 am_pm_group으로 잡히는 경우는 거의 없으나 방어적으로 추가
                hour = 12
        elif hour < 12 and (
            "오후" in original_datetime_str or "저녁" in original_datetime_str
        ):  # 문맥상 오후
            # (단순 추론, "3시"라고만 하면 오전/오후 모호. 프롬프트에서 명확히 유도 필요)
            # 이 부분은 사용자의 의도에 따라 오전/오후를 명확히 구분할 수 없을 때 모호함을 남길 수 있음
            # 필요시 이 heuristic을 제거하거나, 좀 더 정교하게 만들거나, 오후로 강제하는 등의 처리 가능
            pass  # 현재는 24시간제 우선 또는 명시적 오전/오후 키워드 우선

        if minute_group:
            if minute_group == "반":
                minute = 30
            elif minute_group == "정각":
                minute = 0
            else:
                minute = int(minute_group)

        # 24시 처리 (자정 24시는 00시로)
        if hour == 24:
            hour = 0

    else:  # 시간 패턴 매칭 실패 시, HH:MM 형식 또는 일반 parse 시도
        plain_time_match = re.search(
            r"(\d{1,2}:\d{1,2}(:\d{1,2})?)", original_datetime_str
        )
        if plain_time_match:
            time_part_extracted = plain_time_match.group(0)
            date_part_str = original_datetime_str.replace(
                time_part_extracted, ""
            ).strip()
            if not date_part_str:  # 시간만 입력된 경우 (예: "14:30")
                date_part_str = "오늘"

            try:
                time_obj = parse(time_part_extracted).time()
                hour = time_obj.hour
                minute = time_obj.minute
            except (ParserError, ValueError):
                # 시간 파싱 실패 시 LLM으로 처리 시도
                return _call_llm_for_datetime_parsing(
                    original_datetime_str, today_iso_for_llm
                )
        else:
            # 기존의 전체 문자열 대상 parse 시도
            try:
                # dateutil.parser.parse가 "오늘 14:30" 같은 것도 잘 처리할 수 있음
                # 하지만 위에서 "정오", "자정" 및 HH:MM 형식 등을 먼저 걸렀으므로
                # 여기까지 오면 남은 것은 ISO 형식이거나, parse가 처리하기 어려운 형태일 수 있음.
                parsed_dt_obj = parse(original_datetime_str)
                # parse가 날짜만 반환할 수도 있고, 날짜+시간을 반환할 수도 있음.
                # 시간 정보가 없다면 00:00으로 처리됨.
                # 이 함수는 날짜와 '시간' 설명이 모두 있는 문자열을 대상으로 하므로,
                # 여기서 시간 정보가 없다면 의도와 다를 수 있음.
                # 하지만 HTML datetime-local은 항상 T HH:MM을 요구하므로, 아래 strftime은 적절.
                return parsed_dt_obj.strftime("%Y-%m-%dT%H:%M")
            except (ParserError, ValueError):
                # parse 실패 시 LLM으로 처리 시도
                return _call_llm_for_datetime_parsing(
                    original_datetime_str, today_iso_for_llm
                )

    # 2. 날짜 부분 변환 (parse_relative_date_to_iso 사용)
    iso_date_str = parse_relative_date_to_iso(date_part_str)
    if not iso_date_str or not re.match(r"\d{4}-\d{2}-\d{2}", iso_date_str):
        # 날짜 부분 해석 불가시 LLM 시도
        return _call_llm_for_datetime_parsing(original_datetime_str, today_iso_for_llm)

    # 3. YYYY-MM-DDTHH:MM 형식으로 조합
    try:
        # iso_date_str (YYYY-MM-DD) 와 HH, MM을 datetime 객체로 만들어 포맷팅
        final_dt_obj = datetime.strptime(iso_date_str, "%Y-%m-%d").replace(
            hour=hour, minute=minute
        )
        return final_dt_obj.strftime("%Y-%m-%dT%H:%M")
    except ValueError:  # 날짜/시간 조합 오류 (예: 잘못된 시간 값)
        return _call_llm_for_datetime_parsing(original_datetime_str, today_iso_for_llm)


if __name__ == "__main__":
    # test_dates = [
    #     "오늘",
    #     "내일",
    #     "어제",
    #     "모레",
    #     "그저께",
    #     "다음 주 월요일",
    #     "차주 화요일",
    #     "지난 주 수요일",
    #     "전주 목요일",
    #     "이번 주 금요일",
    #     "이번주 토요일",
    #     "금주 일요일",
    #     "이번주월요일",
    #     "다음주수요일",
    #     "2023-12-25",
    #     "12/25/2023",
    #     "2023년 12월 25일",
    #     "12월 25일",
    #     "다음주월요일",
    #     "내일 아침",
    #     "금일",
    #     "명일",
    #     "작일",
    #     "2024년8월5일",  # 붙여쓴 케이스
    # ]

    # print("--- Today is:", datetime.now().date().isoformat(), "---")
    # for test_date in test_dates:
    #     print(
    #         f"Input: '{test_date}', Output: '{parse_relative_date_to_iso(test_date)}'"
    #     )

    # print(f"\n--- Edge Cases ---")
    # print(f"Input: None, Output: '{parse_relative_date_to_iso(None)}'")
    # print(
    #     f"Input: Invalid string, Output: '{parse_relative_date_to_iso('이건 날짜가 아님')}'"
    # )

    # --- datetime_description_to_iso_local 테스트 --- (새로운 섹션으로 추가)
    print("\n--- Testing parse_datetime_description_to_iso_local ---")
    print(f"--- Today is: {datetime.now().date().isoformat()} ---")
    test_datetime_descs = [
        "오늘 오후 3시",  # Expected: YYYY-MM-DDTHH:MM (오늘 15:00)
        "내일 오전 10시 반",  # Expected: YYYY-MM-DDTHH:MM (내일 10:30)
        "모레 2시 15분",  # Expected: YYYY-MM-DDTHH:MM (모레 02:15 또는 14:15 - 오후 명시 없음에 따라, 현재는 02:15)
        "어제 저녁 8시",  # Expected: YYYY-MM-DDTHH:MM (어제 20:00)
        "오늘 14:30",  # Expected: YYYY-MM-DDTHH:MM (오늘 14:30)
        "내일 9시",  # Expected: YYYY-MM-DDTHH:MM (내일 09:00)
        "오늘 정오",  # Expected: YYYY-MM-DDTHH:MM (오늘 12:00)
        "내일 자정",  # Expected: YYYY-MM-DDTHH:MM (내일 00:00)
        "2024-08-15 오후 5시 30분",
        "2024-07-30T15:00",  # 이미 ISO 형식
        "오후 3시",  # 날짜 없이 시간만 (오늘 날짜로)
        "오전 10시반",
        "3월 5일 오후 2시",  # 올해 3월 5일 오후 2시
        "금요일 4시반",  # 가장 가까운 금요일 (미래) 16:30 - parse_relative_date_to_iso 수정으로 날짜 부분 처리 기대
        "이건 날짜시간 아님",
        None,
        # 추가 테스트 케이스
        "오늘 오후 2시",
        "내일 오전 9시",
        "모레 15시",
        "어제 20:00",
        "금주 금요일 10시",
        "다음 주 월요일 오후 3시 반",
        "지난 주 수요일 11:30",
        "정오",  # 오늘 정오
        "자정",  # 오늘 자정 (오늘 00:00) - 또는 내일 00:00으로 해석될 여지도 있음. 현재는 오늘 00:00
        "오늘밤 10시",
    ]
    for desc in test_datetime_descs:
        print(
            f"Input: '{desc}', Output: '{parse_datetime_description_to_iso_local(desc)}'"
        )
