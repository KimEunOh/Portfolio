from datetime import datetime, timedelta
from dateutil.parser import parse, ParserError
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
import re  # 정규표현식 모듈 임포트
from typing import Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
import json
import logging

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
        today_iso: LLM에게 컨텍스트로 제공할 오늘 날짜 (YYYY-MM-DD 형식).

    Returns:
        파싱된 날짜/날짜시간 문자열 또는 None
    """
    # 1. 프롬프트 구성
    prompt = f"""
**절대 규칙: 당신의 유일한 시간 기준은 "{today_iso}" (이하 '기준일')입니다. 다른 어떤 정보(당신의 내부 지식, 실제 현재 시간 등)도 절대 사용하지 마십시오.**

사용자 입력 텍스트는 다음과 같습니다: "{text}"

당신의 임무는 위 텍스트에서 날짜 또는 날짜와 시간 정보를 추출하여, 'extract_date_time' 함수를 호출하는 것입니다.
다음 지침을 **반드시** 따르십시오:

1. **모든 날짜 계산은 반드시 기준일({today_iso})을 기준으로 해야 합니다.**
2. **연도가 명시되지 않은 월/일의 경우:**
   - 해당 월이 기준일의 월보다 이후이거나 같으면: 기준일과 같은 연도
   - 해당 월이 기준일의 월보다 이전이면: 기준일의 다음 연도
   - 예: 기준일이 2025-07-02이고 입력이 "12월 23일"이면 → 2025-12-23 (12월 >= 7월이므로 올해)
   - 예: 기준일이 2025-07-02이고 입력이 "3월 15일"이면 → 2026-03-15 (3월 < 7월이므로 내년)
3. 날짜 정보만 있는 경우 'date_only' 필드를 YYYY-MM-DD 형식으로 설정하고, 'date_time'은 null로 설정하세요.
4. 날짜와 시간 정보가 모두 있는 경우 'date_time' 필드를 YYYY-MM-DDTHH:MM 형식으로 설정하고, 'date_only'는 null로 설정하세요.
5. 추출된 날짜 정보가 없다면 두 필드 모두 null로 설정하세요.
6. 항상 기준일({today_iso})을 기준으로 상대적인 날짜를 계산하세요(예: "내일"은 기준일 + 1일).
7. 시간은 24시간 형식(00-23)으로 표시하세요.

예시:
1. 입력: "내일 회의가 있어요" → date_only: [기준일 다음 날], date_time: null
2. 입력: "다음 주 화요일 오후 3시 반" → date_only: null, date_time: [기준일 기준 다음 주 화요일]T15:30
3. 입력: "2023년 12월 25일에 만나요" → date_only: 2023-12-25, date_time: null
4. 입력: "이번 달 마지막 날 오전 9시" → date_only: null, date_time: [기준일 기준 이번 달 마지막 날]T09:00
5. 기준일이 2025-07-02이고 입력이 "12월 23일"인 경우 → date_only: 2025-12-23
"""

    # 2. Function calling 정의
    functions = [
        {
            "name": "extract_date_time",
            "description": "사용자 입력에서 추출한 날짜 또는 날짜시간 정보",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_only": {
                        "type": "string",
                        "description": "날짜 정보만 있을 때 사용, YYYY-MM-DD 형식",
                    },
                    "date_time": {
                        "type": "string",
                        "description": "날짜와 시간 정보가 모두 있을 때 사용, YYYY-MM-DDTHH:MM 형식",
                    },
                },
                "required": [],
            },
        }
    ]

    try:
        # 3. LLM 호출
        model_with_functions = llm.bind(functions=functions)
        response = model_with_functions.invoke(prompt)

        # LLM 응답 로깅 (디버깅 용도)
        print(f"--- LLM Response for text: '{text}' ---")
        print(f"Response type: {type(response)}")
        if hasattr(response, "content"):
            print(f"Content: {response.content}")
        if hasattr(response, "tool_calls"):
            print(f"Tool calls: {response.tool_calls}")
        if hasattr(response, "additional_kwargs"):
            print(f"Additional kwargs: {response.additional_kwargs}")
        print("-------------------------------------")

        # 4. Function calling 응답 처리 - tool_calls와 function_call 모두 처리
        date_only = None
        date_time = None

        # 4.1 Tool Calls 형식으로 응답이 온 경우 (최신 LangChain)
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_call = response.tool_calls[0]
            if hasattr(tool_call, "args") and isinstance(tool_call.args, dict):
                date_only = tool_call.args.get("date_only")
                date_time = tool_call.args.get("date_time")
            elif hasattr(tool_call, "args") and isinstance(tool_call.args, str):
                # JSON 문자열인 경우 파싱
                try:
                    args = json.loads(tool_call.args)
                    date_only = args.get("date_only")
                    date_time = args.get("date_time")
                except Exception as e:
                    print(f"Error parsing tool_call.args: {e}")

        # 4.2 function_call 형식으로 응답이 온 경우 (이전 버전 호환)
        elif (
            hasattr(response, "additional_kwargs")
            and "function_call" in response.additional_kwargs
        ):
            function_call = response.additional_kwargs["function_call"]
            if "arguments" in function_call:
                try:
                    args = json.loads(function_call["arguments"])
                    date_only = args.get("date_only")
                    date_time = args.get("date_time")
                except Exception as e:
                    print(f"Error parsing function_call arguments: {e}")

        # 4.3 일반 텍스트 응답에서 패턴 추출 (fallback)
        elif hasattr(response, "content") and response.content:
            content = response.content
            # Extract date_time
            dt_pattern = r'date_time[\'"]?\s*[:=]\s*[\'"]?([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2})'
            dt_match = re.search(dt_pattern, content)
            if dt_match:
                date_time = dt_match.group(1)

            # Extract date_only
            do_pattern = r'date_only[\'"]?\s*[:=]\s*[\'"]?([0-9]{4}-[0-9]{2}-[0-9]{2})'
            do_match = re.search(do_pattern, content)
            if do_match:
                date_only = do_match.group(1)

            # 다른 형태의 패턴도 추가 검색
            if not date_time and not date_only:
                iso_pattern = r"([0-9]{4}-[0-9]{2}-[0-9]{2}(?:T[0-9]{2}:[0-9]{2})?)"
                iso_matches = re.findall(iso_pattern, content)
                if iso_matches:
                    for match in iso_matches:
                        if "T" in match:
                            date_time = match
                        else:
                            date_only = match
                        break

        # 5. 결과 반환
        if date_time:
            print(f"Successfully parsed date_time: {date_time}")
            return date_time
        elif date_only:
            print(f"Successfully parsed date_only: {date_only}")
            return date_only
        else:
            print(f"Failed to parse date from text: '{text}'")
            return None

    except Exception as e:
        print(f"Error in _call_llm_for_datetime_parsing: {e}")
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


def parse_relative_date_to_iso(
    date_str: str, current_date_iso: Optional[str] = None
) -> str:
    """다양한 상대적/절대적 날짜 표현을 YYYY-MM-DD 형식으로 변환합니다.
    변환 실패 시 원본 문자열을 반환합니다.
    `current_date_iso`가 제공되면 해당 날짜를 기준으로, 아니면 실제 현재 날짜를 기준으로 합니다.
    """
    if not isinstance(date_str, str):
        return date_str

    if current_date_iso:
        today = datetime.strptime(current_date_iso, "%Y-%m-%d").date()
    else:
        today = datetime.now().date()  # 실제 현재 날짜 사용

    original_date_str = date_str.strip()
    processed_str = original_date_str.lower().replace(" ", "")

    # 1. 매우 간단한 상대 날짜 직접 처리
    if processed_str in ["오늘", "금일"]:
        return today.isoformat()
    if processed_str in ["내일", "명일"]:
        return (today + timedelta(days=1)).isoformat()
    if processed_str in ["어제", "작일"]:
        return (today - timedelta(days=1)).isoformat()
    if processed_str == "모레":
        return (today + timedelta(days=2)).isoformat()
    if processed_str in ["그저께", "그끄제"]:
        return (today - timedelta(days=2)).isoformat()

    # 2. "YYYY년 MM월 DD일", "MM월 DD일", "YYYY-MM-DD", "MM/DD/YYYY" 등 dateutil.parser로 시도
    try:
        # "MM월 DD일" 같은 경우 올해 날짜로 파싱되도록 default를 오늘 날짜로 설정
        # "YYYY년 MM월 DD일" -> "YYYY-MM-DD" 와 같은 전처리
        temp_str = original_date_str
        temp_str = re.sub(
            r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
            lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}",
            temp_str,
        )
        # "MM월 DD일" (앞에 년도 없을 때) -> 스마트 년도 결정
        # 현재 월보다 이전 월이면 다음 년도로, 이후 월이면 올해로 해석
        if not re.match(r"^\d{4}-", temp_str):

            def smart_year_replace(m):
                month = int(m.group(1))
                day = int(m.group(2))
                # 연도가 명시되지 않은 월/일의 경우:
                # - 해당 월이 기준일의 월보다 이후이거나 같으면: 기준일과 같은 연도
                # - 해당 월이 기준일의 월보다 이전이면: 기준일의 다음 연도
                # 예: 기준일이 2025-07-02이고 입력이 "12월 23일"이면 → 2025-12-23 (12 >= 7)
                # 예: 기준일이 2025-07-02이고 입력이 "3월 15일"이면 → 2026-03-15 (3 < 7)
                if month >= today.month:
                    year = today.year  # 현재 월 이후 또는 같으면 올해
                else:
                    year = today.year + 1  # 이전 월이면 다음 년도
                return f"{year}-{month:02d}-{day:02d}"

            temp_str = re.sub(
                r"(\d{1,2})월\s*(\d{1,2})일",
                smart_year_replace,
                temp_str,
            )

        # "오늘 아침", "내일 오후 3시" 등 시간 정보 제거
        time_related_patterns = r"\s*(오전|오후|아침|저녁|밤|새벽|정오|자정|\d{1,2}시(\s*\d{1,2}분)?(\s*\d{1,2}초)?|\d{1,2}:\d{1,2}(:\d{1,2})?|T\d{2}:\d{2}(:\d{2})?)"
        # 시간을 제거하기 전에, "다음 주 월요일 10시" 같은 경우 "다음 주 월요일"은 남겨야 함.
        # 하지만 여기서는 dateutil.parser가 날짜 부분만 잘 파싱할 수 있도록 시간을 제거하는 데 집중.
        temp_str_no_time = re.sub(
            time_related_patterns, "", temp_str, flags=re.IGNORECASE
        ).strip()

        # 만약 시간 제거 후 문자열이 비어있거나, "오늘", "내일" 등으로 바뀐 경우 위에서 처리되었어야 함.
        # 여기서는 dateutil.parser가 날짜로 인식할 수 있는 문자열에 대해서만 시도.
        if temp_str_no_time and not temp_str_no_time.lower().replace(" ", "") in [
            "오늘",
            "금일",
            "내일",
            "명일",
            "어제",
            "작일",
            "모레",
            "그저께",
            "그끄제",
        ]:
            dt = parse(
                temp_str_no_time, default=datetime(today.year, today.month, today.day)
            ).date()
            return dt.isoformat()
    except (ParserError, ValueError):
        pass  # 다음 단계로 넘어감

    # 3. "다음주/차주/지난주/전주/이번주 [요일]" 패턴 처리
    # preprocess_date_str 함수는 시간 정보를 제거하고 "다음 주 월요일" 같은 구문을 남기려고 시도했었음.
    # 해당 로직을 여기에 통합하고 강화.

    # "다음 주 월요일", "이번주 화요일" 등과 같이 시간 표현이 제거된 문자열을 사용
    # `original_date_str`에서 시간 표현만 제거한 버전을 만듬
    cleaned_date_str_for_weekday_logic = re.sub(
        time_related_patterns, "", original_date_str, flags=re.IGNORECASE
    ).strip()

    # 공백 제거 및 소문자화된 버전
    processed_weekday_str = cleaned_date_str_for_weekday_logic.lower().replace(" ", "")

    match = re.match(
        r"(다음주|차주|담주|지난주|전주|금주|이번주|금번주)([월화수목금토일])(요일)?",
        processed_weekday_str,
    )
    if match:
        week_prefix = match.group(1)
        day_char = match.group(2)

        if day_char in DAY_MAP:
            target_weekday_obj = DAY_MAP[day_char]
            today_weekday = today.weekday()  # 월요일 0, 일요일 6

            days_diff = target_weekday_obj.weekday - today_weekday

            if week_prefix in ["다음주", "차주", "담주"]:
                dt = today + timedelta(days=days_diff + 7)
            elif week_prefix in ["지난주", "전주"]:
                dt = today + timedelta(days=days_diff - 7)
            elif week_prefix in ["금주", "이번주", "금번주"]:
                dt = today + timedelta(days=days_diff)
            else:  # "월요일" 등, 요일만 단독으로 온 경우 (가장 가까운 미래의 요일)
                # 이 로직은 위에서 dateutil.parser로 커버될 수 있지만, 명시적으로 처리
                # 또는, "다음"이라는 의미를 내포한다고 가정하고 처리
                if days_diff < 0:  # 이미 지난 요일이면 다음 주의 해당 요일
                    days_diff += 7
                dt = today + timedelta(days=days_diff)
            return dt.isoformat()

    # 4. 단독 요일 처리 (예: "금요일") - 가장 가까운 미래의 해당 요일
    # "금요일" -> processed_str에 저장됨. DAY_MAP 키와 일치하는지 확인
    if processed_str in DAY_MAP:  # DAY_MAP은 "월", "월요일" 등을 키로 가짐
        target_weekday_obj = DAY_MAP[processed_str]
        today_weekday = today.weekday()
        days_diff = target_weekday_obj.weekday - today_weekday
        if days_diff < 0:  # 이미 지난 요일이면 다음 주로
            days_diff += 7
        # 만약 days_diff가 0이면 오늘이 해당 요일. (예: 오늘이 금요일이고 "금요일" 입력)
        # 사용자가 "금요일"이라고만 했다면, 오늘을 포함한 가장 가까운 미래의 금요일을 의미할 가능성이 높음.
        # "오늘"은 위에서 이미 처리. 만약 오늘이 금요일이고 "금요일"이라고 하면 오늘.
        # 하지만 "다음 주 금요일" 등은 위에서 처리.
        # 이 로직은 "금요일에 만나" -> 가장 가까운 금요일 (오늘 포함)
        # 단, 오늘이 금요일이고 "금요일"이라고 했다면 오늘이 되어야 하는데,
        # "오늘"은 이미 위에서 처리됨.
        # "이번 주 금요일"과 그냥 "금요일"의 구분이 모호해질 수 있음.
        # 여기서는 가장 가까운 미래(오늘 포함)의 해당 요일로 해석.
        # 만약 '오늘'인 경우, 이미 맨 위에서 처리되므로, 여기 도달 시 days_diff는 0보다 크거나, 과거 요일이라 +7 된 상태.
        dt = today + timedelta(days=days_diff)
        return dt.isoformat()

    # 5. 모든 규칙 기반 파싱 실패 시 LLM 호출
    # _call_llm_for_datetime_parsing는 "YYYY-MM-DD" 또는 "YYYY-MM-DDTHH:MM"을 반환할 수 있음
    # 여기서는 날짜만 필요하므로, 시간 부분은 제거.
    parsed_by_llm = _call_llm_for_datetime_parsing(original_date_str, today.isoformat())
    if parsed_by_llm:
        # LLM 결과에서 날짜 부분만 추출
        match_llm_date = re.match(r"(\d{4}-\d{2}-\d{2})", parsed_by_llm)
        if match_llm_date:
            return match_llm_date.group(1)

        # 최후의 수단으로 원본 문자열 반환
        return original_date_str


def parse_datetime_description_to_iso_local(
    datetime_str: str, current_date_iso: Optional[str] = None
) -> Optional[str]:
    """
    "내일 오후 3시", "다음 주 월요일 10:00" 같은 설명을 "YYYY-MM-DDTHH:MM" 형식으로 변환합니다.
    `current_date_iso`가 제공되면 해당 날짜를 기준으로, 아니면 실제 현재 날짜를 기준으로 합니다.
    """
    if not datetime_str or not isinstance(datetime_str, str):
        return None

    base_date_iso = (
        current_date_iso if current_date_iso else datetime.now().date().isoformat()
    )
    today = datetime.strptime(base_date_iso, "%Y-%m-%d").date()

    # 1. LLM 기반 파싱 시도
    parsed_by_llm = _call_llm_for_datetime_parsing(datetime_str, base_date_iso)
    if parsed_by_llm:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", parsed_by_llm):
            return parsed_by_llm
        # LLM이 YYYY-MM-DD 형식만 반환했다면, 시간 정보가 없으므로 여기서는 부적합.
        # 하지만 _call_llm_for_datetime_parsing의 프롬프트는 시간을 포함하도록 유도.

    # 2. LLM 실패 시 dateutil.parser를 사용한 규칙 기반 파싱 시도
    try:
        # "오후 3시" -> 오늘 오후 3시, "내일 10시" -> 내일 10시
        # dateutil.parser는 "내일 오후 3시" 등을 잘 파싱함.
        # default를 오늘 날짜/시간으로 설정하여 "오후 3시" 같은 입력도 처리
        # 단, 시간만 있는 경우 오늘 날짜를 기준으로 함.
        # 상대적 날짜 표현(내일, 다음주 등)과 시간 표현이 결합된 경우를 dateutil이 잘 처리.

        # 전처리: "오전 10시 반" -> "오전 10시 30분"
        temp_str = datetime_str.replace("반", "30분")
        temp_str = temp_str.replace("정오", "12시").replace("자정", "0시")

        # "다음 주 월요일 10시" 같은 경우, dateutil.parser가 기준 날짜 없이도 잘 해석할 수 있지만,
        # "10시" 라고만 하면 오늘 10시로 해석.
        # base_date_iso의 날짜 부분을 기준으로 파싱하도록 default 설정
        parsed_dt_obj = parse(
            temp_str, default=datetime(today.year, today.month, today.day)
        )

        # 시간 정보가 있는지 확인. dateutil.parser가 시간 정보를 못 찾으면 00:00:00으로 설정.
        # 원본 문자열에 시간 관련 키워드가 있었는지 확인하여 더 정확하게 판단 가능.
        time_keywords = ["시", "분", "오전", "오후", "정오", "자정", ":"]
        has_time_info_in_input = any(
            keyword in datetime_str for keyword in time_keywords
        )

        if (
            parsed_dt_obj.hour == 0
            and parsed_dt_obj.minute == 0
            and parsed_dt_obj.second == 0
            and not has_time_info_in_input
        ):
            # 시간 정보가 파싱되지 않았고, 입력에도 시간 키워드가 없다면 날짜만 있는 것으로 간주.
            # 이 함수는 날짜+시간을 기대하므로 None 반환.
            return None

        return parsed_dt_obj.strftime("%Y-%m-%dT%H:%M")

    except (ParserError, ValueError):
        return None  # 규칙 기반 파싱도 실패
    except Exception as e:
        print(
            f"Error in parse_datetime_description_to_iso_local (rule-based): {datetime_str}, Error: {e}"
        )
        return None


def parse_date_range_with_context(
    start_date_str: str, end_date_str: str, current_date_iso: Optional[str] = None
) -> tuple[str, str]:
    """날짜 범위를 컨텍스트를 유지하며 파싱합니다.

    "12월 23일부터 25일까지" 같은 경우 start_date의 월 정보를 end_date에 적용합니다.

    Args:
        start_date_str: 시작 날짜 문자열 (예: "12월 23일부터")
        end_date_str: 종료 날짜 문자열 (예: "25일까지")
        current_date_iso: 기준 날짜 (YYYY-MM-DD 형식)

    Returns:
        tuple[str, str]: (파싱된 시작날짜, 파싱된 종료날짜)
    """
    if not isinstance(start_date_str, str) or not isinstance(end_date_str, str):
        return start_date_str, end_date_str

    # 기준 날짜 설정
    if current_date_iso:
        current_date = datetime.strptime(current_date_iso, "%Y-%m-%d").date()
    else:
        current_date = datetime.now().date()

    # 1. start_date 먼저 파싱
    parsed_start = parse_relative_date_to_iso(start_date_str, current_date_iso)

    # 2. end_date에 월 정보가 없고, start_date에 월 정보가 있는 경우 컨텍스트 보강
    if (
        "월" in start_date_str or re.search(r"\d{4}-\d{2}", start_date_str)
    ) and not (  # start_date에 월 정보 있음
        "월" in end_date_str or re.search(r"\d{4}-\d{2}", end_date_str)
    ):  # end_date에 월 정보 없음
        # start_date에서 월 정보 추출
        month_match = re.search(r"(\d{1,2})월", start_date_str)
        year_match = re.search(r"(\d{4})", start_date_str)

        if month_match:
            month = int(month_match.group(1))
            year = int(year_match.group(1)) if year_match else None

            # 년도가 없는 경우 스마트 년도 결정 (parse_relative_date_to_iso와 동일한 로직)
            if year is None:
                if month < current_date.month:
                    year = current_date.year + 1
                else:
                    year = current_date.year

            # end_date에 월 정보 추가
            enhanced_end_date = f"{year}년 {month}월 {end_date_str}"
            parsed_end = parse_relative_date_to_iso(enhanced_end_date, current_date_iso)

            print(
                f"Enhanced end_date with context: '{end_date_str}' → '{enhanced_end_date}' → '{parsed_end}'"
            )
        else:
            # 월 정보 추출 실패 시 일반 파싱
            parsed_end = parse_relative_date_to_iso(end_date_str, current_date_iso)
    else:
        # 일반적인 개별 파싱
        parsed_end = parse_relative_date_to_iso(end_date_str, current_date_iso)

    return parsed_start, parsed_end


def parse_duration_to_days(text: str) -> Optional[float]:
    """문자열에서 기간을 추출하여 '일' 단위로 변환합니다.
    'X월 Y일' 같은 날짜 표현을 기간으로 오인하지 않도록 주의합니다.

    Args:
        text: 기간을 나타내는 문자열 (예: "3일", "일주일", "2주간", "반나절")

    Returns:
        변환된 일수(float) 또는 변환 실패 시 None
    """
    if not isinstance(text, str):
        return None

    text = text.strip()
    value = None

    # 1. 'X월 Y일' 형식의 날짜 패턴인지 먼저 확인. 날짜면 기간이 아님.
    if re.search(r"\d{1,2}\s*월\s*\d{1,2}\s*일", text):
        logging.info(f"'{text}' is considered a date, not a duration. Skipping.")
        return None

    # 2. 날짜가 아닐 경우, 기간 파싱 시도
    # 숫자 기반 기간 (예: 3일, 2주, 1개월)
    match = re.search(r"(\d+(\.\d+)?)\s*(시간|일|주|달|개월|년)", text)
    if match:
        num = float(match.group(1))
        unit = match.group(3)

        if unit == "시간":
            value = num / 24  # 시간은 일로 변환
        elif unit == "일":
            value = num
        elif unit == "주":
            value = num * 7
        elif unit in ["달", "개월"]:
            value = num * 30  # 근사치
        elif unit == "년":
            value = num * 365  # 근사치
    else:
        # 텍스트 기반 기간 (예: 하루, 일주일, 반나절)
        duration_map = {
            "하루": 1,
            "이틀": 2,
            "사흘": 3,
            "나흘": 4,
            "닷새": 5,
            "엿새": 6,
            "일주일": 7,
            "한달": 30,
            "두달": 60,
            "반나절": 0.5,
            "반차": 0.5,
        }
        for key, days in duration_map.items():
            if key in text:
                value = float(days)
                break

    if value is not None:
        logging.info(f"Parsed duration '{text}' to {value} days.")
    else:
        logging.warning(f"Failed to parse duration from '{text}'.")

    return value


if __name__ == "__main__":
    # parse_relative_date_to_iso 테스트용 today 설정 (테스트 일관성)
    fixed_today_for_test = "2025-05-22"  # 목요일

    test_dates = [
        ("오늘", fixed_today_for_test),
        ("내일", fixed_today_for_test),
        ("어제", fixed_today_for_test),
        ("모레", fixed_today_for_test),
        ("그저께", fixed_today_for_test),
        ("2023-12-25", fixed_today_for_test),
        ("12/25/2023", fixed_today_for_test),
        ("2023년 12월 25일", fixed_today_for_test),
        ("12월 25일", fixed_today_for_test),  # 올해 12월 25일 (2025-12-25)
        ("1월 5일", fixed_today_for_test),  # 올해 1월 5일 (2025-01-05)
        ("다음 주 월요일", fixed_today_for_test),  # 2025-05-26
        ("차주 화요일", fixed_today_for_test),  # 2025-05-27
        ("지난 주 수요일", fixed_today_for_test),  # 2025-05-14
        ("전주 목요일", fixed_today_for_test),  # 2025-05-15
        ("이번 주 금요일", fixed_today_for_test),  # 2025-05-23
        ("이번주 토요일", fixed_today_for_test),  # 2025-05-24
        ("금주 일요일", fixed_today_for_test),  # 2025-05-25
        ("월요일", fixed_today_for_test),  # 가장 가까운 월요일 (2025-05-26)
        (
            "수요일",
            fixed_today_for_test,
        ),  # 가장 가까운 수요일 (2025-05-28). fixed_today_for_test(목)
        ("목요일", fixed_today_for_test),  # 오늘 (2025-05-22)
        ("내일 아침 9시", fixed_today_for_test),  # 날짜만 추출해야 함 -> 2025-05-23
        ("2024년8월5일", fixed_today_for_test),
        ("다음 달 첫째 주 월요일", fixed_today_for_test),  # LLM 호출 대상
        ("지난 달 마지막 금요일", fixed_today_for_test),  # LLM 호출 대상
        (
            "다다음주 수요일",
            fixed_today_for_test,
        ),  # "다다음주"는 현재 규칙에 없음. LLM 호출 대상
    ]

    print(
        f"--- Testing parse_relative_date_to_iso (기준일: {fixed_today_for_test}) ---"
    )
    for test_date_str, test_current_date in test_dates:
        print(
            f"Input: '{test_date_str}', Output: '{parse_relative_date_to_iso(test_date_str, test_current_date)}'"
        )

    print(
        f"\n--- Edge Cases for parse_relative_date_to_iso (기준일: {fixed_today_for_test}) ---"
    )
    print(
        f"Input: None, Output: '{parse_relative_date_to_iso(None, fixed_today_for_test)}'"
    )
    print(
        f"Input: Invalid string, Output: '{parse_relative_date_to_iso('이건 날짜가 아님', fixed_today_for_test)}'"  # LLM 호출
    )

    # --- parse_datetime_description_to_iso_local 테스트 ---
    print(
        "\n--- Testing parse_datetime_description_to_iso_local (기준일: {fixed_today_for_test}) ---"
    )
    test_datetime_descs = [
        ("오늘 오후 3시", fixed_today_for_test),
        ("내일 오전 10시 반", fixed_today_for_test),
        (
            "모레 2시 15분",
            fixed_today_for_test,
        ),  # "2시"는 오전/오후 모호. dateutil은 AM으로 해석하는 경향.
        ("어제 저녁 8시", fixed_today_for_test),
        ("오늘 14:30", fixed_today_for_test),
        ("내일 9시", fixed_today_for_test),
        ("오늘 정오", fixed_today_for_test),
        ("내일 자정", fixed_today_for_test),  # dateutil은 다음날 00:00으로 해석
        ("2024-08-15 오후 5시 30분", fixed_today_for_test),
        ("2024-07-30T15:00", fixed_today_for_test),
        ("오후 3시", fixed_today_for_test),  # 오늘 오후 3시
        ("오전 10시반", fixed_today_for_test),  # 오늘 오전 10시 30분
        ("3월 5일 오후 2시", fixed_today_for_test),  # 2025-03-05T14:00
        (
            "금요일 4시반",
            fixed_today_for_test,
        ),  # 2025-05-23T16:30 (가장 가까운 금요일 오후 4시반)
        (
            "이건 날짜시간 아님",
            fixed_today_for_test,
        ),  # LLM 시도 후 None 또는 규칙 기반 None
        (None, fixed_today_for_test),
        ("다음 주 월요일 오후 3시 반", fixed_today_for_test),  # 2025-05-26T15:30
        ("지난 주 수요일 11:30", fixed_today_for_test),  # 2025-05-14T11:30
    ]
    for desc_str, test_current_date in test_datetime_descs:
        print(
            f"Input: '{desc_str}', Output: '{parse_datetime_description_to_iso_local(desc_str, test_current_date)}'"
        )
