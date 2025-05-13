"""
일반 챗봇 및 연차 신청 처리 통합 에이전트 모듈

이 모듈은 일반적인 대화 처리와 연차 신청 의도 파악, 연차 신청 처리를 통합한 에이전트를 구현합니다.
"""

import os
import json
import logging
import traceback
import sys
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, TypedDict, Optional, Annotated
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from enum import Enum
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
import httpx
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RunnableConfig

# ------------------------------------------------------
# 1. 기본 설정
# ------------------------------------------------------

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("general_chatbot_debug.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,  # 기존 로깅 설정을 강제로 재설정
)

# 로거 설정
logger = logging.getLogger("general_chatbot")
logger.setLevel(logging.DEBUG)

# 로그 핸들러 설정
for handler in logger.handlers:
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    if isinstance(handler, logging.FileHandler):
        handler.setEncoding("utf-8")

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper")

# LLM 초기화를 위한 전역 변수
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
general_graph = None

# 세션별 초기화 상태를 저장하는 전역 딕셔너리
initialized_sessions = {}


# 연차 종류 정의
class VacationType(Enum):
    DAY = "연차"
    HALF_AM = "오전반차"
    HALF_H_AM = "오전반반차"
    HALF_PM = "오후반차"
    HALF_H_PM = "오후반반차"


# 연차 일정 정보
class DayList(TypedDict):
    reqYmd: str
    dvType: str


# 결재 라인 정보
class LineList(TypedDict):
    aprvPsId: str
    aprvPsNm: str  # 추가: 승인자 이름
    aprvDvTy: str  # 결재 종류
    ordr: int  # 결재 순서


# 문서 정보
class DocumentInfo(TypedDict):
    mstPid: int
    aprvNm: str
    drafterId: str
    docCn: str  # 사유
    dayList: DayList
    lineList: LineList


def vacation_info_merger(existing_info, new_info):
    """vacation_info를 병합하는 맞춤형 함수"""
    if new_info is None:
        logger.info("vacation_info 완전 초기화 신호 감지")
        # 기본값만 있는 새로운 객체 반환
        return {"drafterId": "01180001", "mstPid": 1}

    if not existing_info:
        return new_info

    result = existing_info.copy()

    # 새 정보의 필드 업데이트
    for key, value in new_info.items():
        # None 값을 특정 필드의 초기화 신호로 처리
        if value is None and key in result:
            # 필드 타입에 따른 초기화
            if isinstance(result[key], list):
                result[key] = []  # 리스트는 빈 리스트로 초기화
            elif isinstance(result[key], dict):
                result[key] = {}  # 딕셔너리는 빈 딕셔너리로 초기화
            elif isinstance(result[key], str):
                result[key] = ""  # 문자열은 빈 문자열로 초기화
            elif isinstance(result[key], (int, float)):
                result[key] = 0  # 숫자는 0으로 초기화
            else:
                result[key] = None  # 기타 타입은 None으로 초기화
        elif value is not None:
            # None이 아닌 경우 정상 업데이트
            result[key] = value

    # dayList와 같은 특수 필드 처리
    if "dayList" in new_info:
        if new_info["dayList"] is None:
            result["dayList"] = []  # None인 경우 빈 리스트로 초기화
        elif new_info["dayList"]:
            result["dayList"] = new_info["dayList"]  # 값이 있으면 업데이트

    return result


# 마지막 값을 유지하는 함수
def last_value(existing, new):
    return new


# 에이전트 상태 정의
class GeneralAgentState(TypedDict):
    """에이전트 상태 정의"""

    messages: Annotated[list, add_messages]
    vacation_info: Annotated[DocumentInfo, vacation_info_merger]
    next: Annotated[str, last_value]
    thread_id: Annotated[str, last_value]


class Router(TypedDict):
    """다음에 호출할 작업자. 더 이상 작업자가 필요하지 않으면 FINISH를 반환"""

    next: Literal["FINISH", "VACATION_REQUEST", "GENERAL_CHAT"]


# 연차 관련 API 요청 모델들
class EmployeeInfoRequest(BaseModel):
    drafterId: str = Field(..., description="직원 ID")


members = ["VACATION_REQUEST", "GENERAL_CHAT"]
option = members + ["FINISH"]

# ------------------------------------------------------
# 2. API 관련 모듈
# ------------------------------------------------------


class ApiClient:
    """API 클라이언트 클래스"""

    def __init__(self, api_url):
        self.api_url = api_url
        self.client = httpx.Client(timeout=30)

    def call_api(self, endpoint: str, method: str, params: Dict = None) -> Dict:
        """API 호출 함수"""
        logger.info(f"API 호출 시작: {method} {endpoint}")
        logger.debug(f"API 파라미터: {params}")

        try:
            url = f"{self.api_url}/{endpoint}"
            logger.debug(f"완전한 URL: {url}")

            headers = {"Content-Type": "application/json"}

            if method.upper() == "GET":
                response = self.client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = self.client.post(url, json=params, headers=headers)
            elif method.upper() == "PUT":
                response = self.client.put(url, json=params, headers=headers)
            else:
                return {"error": f"지원하지 않는 HTTP 메서드: {method}", "code": "-1"}

            response.raise_for_status()
            return response.json()

        except Exception as e:
            error_msg = f"API 호출 오류: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "code": "-1"}


# API 클라이언트 인스턴스 생성
api_client = ApiClient(API_BASE_URL)


# API 직접 호출 함수들
def fetch_employee_info(drafterId: str) -> Dict:
    """직원 정보를 직접 API로 조회합니다."""
    logger.info(f"직원 정보 조회: drafterId={drafterId}")
    try:
        # 실제로는 API 호출해야 하지만 현재는 예시 데이터 반환
        return {
            "drafterId": drafterId,
            "name": "홍길동",
            "department": "개발팀",
            "position": "책임",
            "hire_date": "2015-01-01",
        }
    except Exception as e:
        logger.error(f"직원 정보 조회 오류: {str(e)}")
        return {"error": str(e), "code": "-1"}


def fetch_remaining_vacation_days(drafterId: str) -> Dict:
    """직원의 잔여 연차 일수를 직접 API로 조회합니다."""
    logger.info(f"잔여 연차 조회: drafterId={drafterId}")
    try:
        endpoint = "remainder"
        method = "POST"
        params = {"drafterId": drafterId}

        result = api_client.call_api(endpoint, method, params)

        # API 실패 시 예시 데이터 사용
        if "error" in result:
            logger.warning("API 호출 실패, 예시 데이터 사용")
            return {
                "drafterId": drafterId,
                "total_days": 15,
                "used_days": 7,
                "remaining_days": 8,
            }

        return result
    except Exception as e:
        logger.error(f"잔여 연차 조회 오류: {str(e)}")
        return {
            "error": str(e),
            "code": "-1",
            "drafterId": drafterId,
            "remaining_days": "조회 실패",
        }


def fetch_approval_line(drafterId: str) -> Dict:
    """직원의 결재 라인을 직접 API로 조회합니다."""
    logger.info(f"결재 라인 조회: drafterId={drafterId}")
    try:
        endpoint = "myLine"
        method = "POST"
        params = {"mstPid": 1, "drafterId": drafterId}

        result = api_client.call_api(endpoint, method, params)

        # API 실패 시 예시 데이터 사용
        if "error" in result:
            logger.warning("API 호출 실패, 예시 데이터 사용")
            return {
                "code": 1,
                "message": "결재 라인 조회",
                "data": [
                    {
                        "aprvPsId": "01150001",
                        "aprvPsNm": "김팀장",
                        "aprvDvTy": "AGREEMENT",
                        "ordr": 1,
                    },
                    {
                        "aprvPsId": "01120001",
                        "aprvPsNm": "이부장",
                        "aprvDvTy": "AGREEMENT",
                        "ordr": 2,
                    },
                ],
            }

        return result
    except Exception as e:
        logger.error(f"결재 라인 조회 오류: {str(e)}")
        return {
            "error": str(e),
            "code": "-1",
            "drafterId": drafterId,
            "approval_line": "조회 실패",
        }


def fetch_existing_vacations(drafterId: str) -> Dict:
    """직원의 기존 휴가 신청 목록을 직접 API로 조회합니다."""
    logger.info(f"기존 휴가 조회: drafterId={drafterId}")
    try:
        # 실제로는 API 호출해야 하지만 현재는 예시 데이터 반환
        return {
            "drafterId": drafterId,
            "vacations": [
                {
                    "id": "V2024001",
                    "type": "연차",
                    "start_date": "2024-04-22",
                    "end_date": "2024-04-22",
                    "status": "승인완료",
                },
                {
                    "id": "V2024002",
                    "type": "반차(오후)",
                    "start_date": "2024-05-10",
                    "end_date": "2024-05-10",
                    "status": "승인대기",
                },
            ],
        }
    except Exception as e:
        logger.error(f"기존 휴가 조회 오류: {str(e)}")
        return {"error": str(e), "code": "-1"}


def submit_vacation_request_to_api(request_json: Dict) -> Dict:
    """연차 신청 요청을 API로 전송합니다."""
    logger.info(f"연차 신청 요청: {request_json}")
    try:
        endpoint = "register"
        method = "PUT"

        result = api_client.call_api(endpoint, method, request_json)

        # API 실패 시 예시 데이터 사용
        if "error" in result:
            logger.warning("API 호출 실패, 예시 데이터 사용")
            return {
                "success": True,
                "document_id": "V2024010",
                "status": "승인대기",
                "message": "연차 신청이 완료되었습니다.",
            }

        return result
    except Exception as e:
        logger.error(f"연차 신청 오류: {str(e)}")
        return {
            "error": str(e),
            "code": "-1",
            "message": "연차 신청 처리 중 오류가 발생했습니다.",
        }


# ------------------------------------------------------
# 3. 유틸리티 함수
# ------------------------------------------------------


def map_vacation_type(user_type: str) -> str:
    """사용자 입력 연차 타입을 시스템 코드로 변환합니다."""
    # 사용자 입력값을 소문자로 변환하여 비교
    type_lower = user_type.lower()

    # 각 타입 매핑
    if "오전" in type_lower and "반반" in type_lower:
        return "HALF_H_AM"
    elif "오전" in type_lower and "반차" in type_lower:
        return "HALF_AM"
    elif "오후" in type_lower and "반반" in type_lower:
        return "HALF_H_PM"
    elif "오후" in type_lower and "반차" in type_lower:
        return "HALF_PM"
    elif "연차" in type_lower:
        return "DAY"

    # 기본값은 연차
    return "DAY"


def create_day_list(start_date: str, end_date: str, vacation_type: str) -> List[Dict]:
    """
    시작일과 종료일 정보로 dayList 배열을 생성합니다.

    Args:
        start_date: 휴가 시작일(YYYY-MM-DD)
        end_date: 휴가 종료일(YYYY-MM-DD), 없으면 시작일과 동일
        vacation_type: 휴가 유형

    Returns:
        List[Dict]: dayList 배열
    """
    # 종료일이 없으면 시작일로 설정
    if not end_date:
        end_date = start_date

    day_list = []

    # 날짜 형식 검증
    if not start_date or not end_date:
        return day_list

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # 같은 날짜면 하루만 추가
        if start_date == end_date:
            day_list.append(
                {"reqYmd": start_date, "dvType": map_vacation_type(vacation_type)}
            )
        else:
            # 날짜 범위에 대해 각 날짜 추가
            current = start
            while current <= end:
                day_list.append(
                    {
                        "reqYmd": current.strftime("%Y-%m-%d"),
                        "dvType": map_vacation_type(vacation_type),
                    }
                )
                current += timedelta(days=1)
    except ValueError as e:
        logger.error(f"날짜 형식 오류: {e}")
        return []

    return day_list


# 제출 완료 후 카드 HTML 생성 함수
def create_vacation_card_html(
    document_info: DocumentInfo,
    employee_info: Dict,
    remaining_days: Any,
) -> Dict:
    """
    연차 신청 정보를 HTML 카드로 생성합니다.
    """
    try:
        # 시작일과 종료일 정보 가져오기
        start_date = document_info.get("start_date", "")
        end_date = document_info.get("end_date", "")

        # 날짜 표시 형식 설정
        if start_date and end_date:
            if start_date == end_date:
                date_display = f"{start_date}"
            else:
                date_display = f"{start_date} ~ {end_date}"
        else:
            date_display = ""

        # 사유 정보 가져오기
        reason = document_info.get("docCn", "")

        # 결재자 정보 형식화
        approvers = []
        for approver in document_info.get("lineList", []):
            approvers.append(
                f"{approver.get('aprvPsNm', '')} ({approver.get('aprvDvTy', '')})"
            )
        approvers_text = ", ".join(approvers)

        html = f"""
    <div class="vacation-card">
        <h3>🗓️ 연차 신청 정보</h3>
        
        <div class="info-row">
            <div class="label">신청자</div>
            <div class="value">{employee_info.get("name", "이름 없음")} {employee_info.get("position", "")}</div>
        </div>
        
        <div class="info-row">
            <div class="label">부서</div>
            <div class="value">{employee_info.get("department", "부서 정보 없음")}</div>
        </div>
        
        <div class="info-row">
            <div class="label">휴가 종류</div>
            <div class="value">{document_info.get("dvType", "")}</div>
        </div>
        
        <div class="info-row">
            <div class="label">기간</div>
            <div class="value">{date_display}</div>
        </div>
        
        <div class="info-row">
            <div class="label">사유</div>
            <div class="value">{reason}</div>
        </div>
        
        <div class="approvers">
            <div class="label">결재자</div>
            <div>{approvers_text}</div>
        </div>
        
        <div class="remain-days">
            남은 연차: {remaining_days.get("remaining_days", "0")}일
        </div>
    </div>
    """

        logger.info(html)
        return html
    except Exception as e:
        logger.error(f"HTML 카드 생성 중 오류: {str(e)}")
        return f"<div>연차 정보 카드 생성 중 오류 발생: {str(e)}</div>"


def create_vacation_request_json(
    document_info: DocumentInfo,
    employee_info: Dict,
) -> Dict:
    """
    연차 신청을 위한 API 요청 JSON을 생성합니다.

    Args:
        document_info: 문서 정보
        employee_info: 직원 정보

    Returns:
        Dict: API 요청용 JSON 데이터
    """
    logger.info(f"연차 신청 JSON 생성: drafterId={employee_info.get('drafterId', '')}")

    current_info = document_info.copy()

    # 결재선 리스트 생성
    line_list = []
    for idx, approver in enumerate(current_info.get("lineList", [])):
        # 결재 타입은 모두 "APPROVAL"로 설정
        approval_type = "APPROVAL"
        line_list.append(
            {
                "aprvPsId": approver.get("id", ""),
                "aprvDvTy": approval_type,
                "ordr": idx + 1,
            }
        )

    # 최종 JSON 생성 (필드명과 데이터 타입을 이미지의 명세에 맞게 조정)
    request_json = {
        "mstPid": current_info.get("mstPid", ""),
        "aprvNm": f"{current_info.get('dvType', '연차')} 신청",
        "drafterId": employee_info.get("drafterId", ""),
        "docCn": current_info.get("docCn", ""),
        "dayList": current_info.get("dayList", []),
        "lineList": line_list,
    }

    logger.info(
        f"생성된 연차 신청 JSON: {json.dumps(request_json, ensure_ascii=False)}"
    )
    return request_json


# ------------------------------------------------------
# 4. LLM 기반 도구 및 노드 함수
# ------------------------------------------------------


# ------------------------------------------------------
# 5. 메인 함수 및 그래프 생성
# ------------------------------------------------------


# SuperVisor 노드 생성
def supervisor_node(state: GeneralAgentState):
    """
    사용자 메시지를 처리하고 현재 의도를 결정하는 함수입니다.
    """

    user_input = interrupt({"text_to_revise": state["messages"]})
    state["messages"].append(HumanMessage(content=user_input))

    system_prompt = """
    당신은 사용자 요청을 관리하는 Supervisor입니다. 
    다음 작업자들을 관리합니다: VACATION_REQUEST, GENERAL_CHAT

    VACATION_REQUEST : 사용자가 연차 신청작업과 관련된 내용을 입력할 때 호출합니다.
    GENERAL_CHAT : 사용자가 일반적인 내용을 입력할 때 호출합니다.

    주어진 사용자 메시지를 분석하고, 다음에 호출할 작업자를 결정하세요.
    각 작업자는 작업을 수행하고 결과와 상태를 반환합니다.
    작업자의 작업이 한번이라도 완료되면 FINISH를 반환합니다.
    """
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]

    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]

    # END 반환 방식 수정
    if goto == "FINISH":
        goto = END

    return {"next": goto}


# 연차 정보 수집 노드
def vacation_info_collector(state: GeneralAgentState):
    """
    연차 정보를 수집하는 노드입니다.
    """
    # 전역 변수 사용 선언
    global initialized_sessions

    # 현재 세션 ID 가져오기
    thread_id = state.get("thread_id", "default")

    # 초기 설정 (처음 실행 시에만)
    if thread_id not in initialized_sessions or not initialized_sessions[thread_id]:
        logger.info(f"vacation_info_collector 초기화 시작: thread_id={thread_id}")

        # 직원 정보와 남은 연차 정보 가져오기
        employee_info = fetch_employee_info(state["vacation_info"]["drafterId"])
        remaining_days = fetch_remaining_vacation_days(
            state["vacation_info"]["drafterId"]
        )
        approval_line = fetch_approval_line(state["vacation_info"]["drafterId"])

        # 결재선 정보 저장
        state["vacation_info"]["lineList"] = approval_line.get("data", [])

        # 전역 변수에 초기화 완료 표시
        initialized_sessions[thread_id] = True
        logger.info(f"vacation_info_collector 초기화 완료: thread_id={thread_id}")

        # 초기 안내 메시지
        response = (
            f"안녕하세요 {employee_info.get('name', '홍길동')}님, "
            f"현재 남은 연차는 {remaining_days.get('remaining_days', '조회 실패')}일 입니다. "
            "연차 신청을 원하시는 경우 다음 정보를 알려주세요:\n"
            "1. 연차 종류 (연차/오전반차/오후반차 등)\n"
            "2. 시작 날짜\n"
            "3. 종료 날짜 (하루만 쓰시는 경우 시작 날짜와 동일)\n"
            "4. 사유"
        )

        state["response"] = response
        state["messages"].append(AIMessage(content=response))

        # 폼 초기화
        if "vacation_info" not in state or not state["vacation_info"]:
            state["vacation_info"] = {
                "dvType": None,
                "start_date": None,
                "end_date": None,
                "docCn": None,
                "dayList": [],
            }

        # 인터럽트 호출 - 사용자 입력을 기다림
        user_input = interrupt({"text_to_revise": state["messages"]})
        logger.info(f"인터럽트 호출 - vacation_info_collector: {user_input}")

        # 재개 직후 로깅 및 플래그 초기화
        logger.info(f"인터럽트 후 재개 - user_input: {user_input}")

        # 인터럽트 후 재개될 때 실행되는 부분
        state["messages"].append(HumanMessage(content=user_input))

        state["interrupted"] = False
        state["messages"] = state["messages"]

        state["next"] = "vacation_info_collector"
        # 사용자 입력을 기다리도록 interrupt 호출
        return state

    # 이미 초기화된 경우 다음 노드로 이동
    state["next"] = "vacation_info_collector"
    return state


# 연차 정보 추출 노드
def vacation_info_extractor(state: GeneralAgentState):
    """
    사용자 입력에서 연차 정보를 추출하는 노드입니다.
    """
    # 가장 최근 사용자 메시지 가져오기
    user_input = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_input = msg.content
            break

    logger.info(f"최근 사용자 입력: {user_input}")

    # 모델을 사용해 입력에서 정보 추출
    extracted_info = llm.invoke(
        f"""사용자 입력: {user_input}
        사용자 입력에서 다음 정보들을 추출하세요.
        - 연차 종류 (연차, 오전반차, 오후반차 등) -> dvType 필드에 저장
        - 시작 날짜 (YYYY-MM-DD 형식으로 변환, 예: 2025-04-20) -> start_date 필드에 저장
        - 종료 날짜 (YYYY-MM-DD 형식으로 변환) -> end_date 필드에 저장
        - 사유 -> docCn 필드에 저장   
        존재하는 정보만 추출하고, 없는 정보는 추출하지 마세요.
        JSON 형식으로 반환하세요. 반드시 YYYY-MM-DD 형식으로 날짜를 변환하세요.
        4월 20일과 같은 날짜는 2025-04-20으로 변환해야 합니다.
        만약 연도가 없으면 2025년으로 가정하세요.

        예시 :
        user_input : 연차 4월 20일 개인 사정
        {{
            "dvType": "연차",
            "start_date": "2025-04-20",
            "end_date": "2025-04-20",
            "docCn": "개인 사정"
        }},
        user_input : 연차 4월 20일
        {{
            "dvType": "연차",
            "start_date": "2025-04-20",
            "end_date": "2025-04-20",
            "docCn": null
        }}
        
        결과를 정확한 JSON 형식으로만 반환하세요. 다른 설명이나 마크다운 포맷은 사용하지 마세요.
        """
    )

    # JSON 파싱 (수정된 부분)
    import json

    # LLM 응답 확인
    logger.debug(f"LLM 응답: {extracted_info}")

    # 기존 폼 상태 가져오기 (중요: 기존 상태 유지)
    current_form = state["vacation_info"].copy()

    try:
        # AIMessage 객체인 경우 content 속성 접근
        content = ""
        if isinstance(extracted_info, (str, bytes, bytearray)):
            content = extracted_info
        elif hasattr(extracted_info, "content"):
            content = extracted_info.content

        # 코드 블록 제거 (```json과 ``` 마크다운 블록 제거)
        content = content.replace("```json", "").replace("```", "").strip()
        logger.debug(f"정제된 콘텐츠: {content}")

        # JSON 블록 추출을 위한 정규식
        import re

        json_pattern = r"({[^}]*})"
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            json_str = match.group(1)
            logger.debug(f"추출된 JSON 문자열: {json_str}")
            new_info = json.loads(json_str)
        else:
            # 정규식으로 매칭되지 않으면 전체 콘텐츠로 시도
            new_info = json.loads(content)

        # 날짜 정보가 있으면 dayList 생성
        if "start_date" in new_info and new_info["start_date"]:
            end_date = new_info.get("end_date", new_info["start_date"])
            day_list = create_day_list(
                new_info["start_date"],
                end_date,
                new_info.get("dvType", current_form.get("dvType", "연차")),
            )
            new_info["dayList"] = day_list

        # 중요: 새 정보만 업데이트하고 기존 정보는 유지
        for key, value in new_info.items():
            if (
                value and value != "null" and value != "None"
            ):  # 값이 있는 경우만 업데이트
                current_form[key] = value

        state["vacation_info"] = current_form
        logger.info(f"추출된 정보: {new_info}")

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        response = "입력하신 정보를 이해하지 못했습니다. 다시 명확하게 알려주세요."
        state["response"] = response
        state["messages"].append(AIMessage(content=response))
        state["next"] = "vacation_info_collector"
        return state

    # 업데이트된 정보 저장
    state["vacation_info"] = current_form
    logger.info(f"현재 정보: {current_form}")

    field_name_map = {
        "dvType": "연차 종류",
        "start_date": "시작 날짜",
        "end_date": "종료 날짜",
        "docCn": "사유",
    }

    # 부족한 정보가 있는지 확인
    missing_fields = []
    required_fields = ["dvType", "start_date", "docCn"]  # 필수 필드만 체크

    for key in required_fields:
        if key not in current_form or not current_form[key]:
            missing_fields.append(field_name_map[key])

    if missing_fields:
        logger.warning(f"다음 필드에 값이 없습니다: {', '.join(missing_fields)}")
        response = f"다음 정보를 추가로 알려주세요:\n" + "\n".join(
            f"- {field}" for field in missing_fields
        )
        state["response"] = response
        state["messages"].append(AIMessage(content=response))
        state["vacation_info"] = current_form  # 현재 상태 저장

        state["next"] = "vacation_info_collector"
        return state
    # 모든 필수 정보가 있으면 확인 노드로 이동
    state["vacation_info"] = current_form  # 상태 업데이트를 먼저 수행
    # next 키만 반환
    state["next"] = "vacation_confirmer"
    return state


# 연차 확인 노드
def vacation_confirmer(state: GeneralAgentState):
    """
    연차 신청 정보를 사용자에게 확인하는 노드입니다.
    """
    # HTML 카드 생성
    employee_info = fetch_employee_info(state["vacation_info"]["drafterId"])
    remaining_days = fetch_remaining_vacation_days(state["vacation_info"]["drafterId"])

    response = create_vacation_card_html(
        document_info=state["vacation_info"],
        employee_info=employee_info,
        remaining_days=remaining_days,
    )

    state["response"] = response
    state["messages"].append(AIMessage(content=response))

    # 확인 메시지 전송
    confirm_msg = (
        f"다음 정보로 연차를 신청하시겠습니까?\n\n"
        f"{response}\n\n"
        f"확인하시면 '예'를, 수정하시려면 '아니오'를 입력해주세요."
    )

    state["response"] = confirm_msg
    state["messages"].append(AIMessage(content=confirm_msg))

    # 인터럽트 호출 - 사용자 입력을 기다림
    user_input = interrupt({"text_to_revise": state["messages"]})
    logger.info(f"인터럽트 호출 - vacation_confirmer: {user_input}")

    # 재개 직후 플래그 초기화
    logger.info("인터럽트 후 재개 - interrupted=False 설정")

    state["messages"].append(HumanMessage(content=user_input))

    state["interrupted"] = False
    state["messages"] = state["messages"]
    state["vacation_info"] = state["vacation_info"]

    # 인터럽트 후 상태 업데이트
    state["next"] = "vacation_submitter"
    return state


# 연차 제출 노드
def vacation_submitter(state: GeneralAgentState):
    """
    연차 신청을 제출하는 노드입니다.
    """
    # 가장 최근 사용자 메시지 가져오기
    user_input = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_input = msg.content
            break

    logger.info(f"확인 메시지에 대한 사용자 응답: {user_input}")

    # '예'로 응답한 경우 - 연차 신청 진행
    if (
        "예" in user_input.lower()
        or "네" in user_input.lower()
        or "신청" in user_input.lower()
    ):
        logger.info("사용자가 연차 신청을 확인함")

        # 연차 유형을 영문으로 변환
        vacation_type_map = {
            "연차": VacationType.DAY,
            "오전반차": VacationType.HALF_AM,
            "오전반반차": VacationType.HALF_H_AM,
            "오후반차": VacationType.HALF_PM,
            "오후반반차": VacationType.HALF_H_PM,
        }

        if state["vacation_info"]["dvType"] in vacation_type_map:
            state["vacation_info"]["dvType"] = vacation_type_map[
                state["vacation_info"]["dvType"]
            ].name
        else:
            logger.error(f"알 수 없는 연차 종류: {state['vacation_info']['dvType']}")
            response = "알 수 없는 연차 종류입니다. 다시 입력해주세요."
            state["response"] = response
            state["messages"].append(AIMessage(content=response))
            state["next"] = "vacation_info_collector"
            return state

        # 연차 신청 API 호출
        submit_vacation_request_to_api(state["vacation_info"])
        response = "연차 신청이 완료되었습니다."
        state["response"] = response
        state["messages"].append(AIMessage(content=response))

        # 초기화 상태 재설정
        thread_id = state.get("thread_id", "default")
        initialized_sessions[thread_id] = False
        logger.info(f"vacation_submitter 작업 완료: thread_id={thread_id}")

        state["next"] = END
        return state
    else:
        # '아니오'로 응답한 경우 - 취소 메시지
        logger.info("사용자가 연차 신청을 취소함")
        response = "연차 신청을 취소하셨습니다. 다시 처음부터 정보를 입력하시려면 '연차'라고 입력해주세요."
        state["response"] = response
        state["messages"].append(AIMessage(content=response))

        # 초기화 상태 재설정
        thread_id = state.get("thread_id", "default")
        initialized_sessions[thread_id] = False
        logger.info(f"연차 신청 취소로 세션 초기화: thread_id={thread_id}")

        state["next"] = END
        return state


def general_chat_agent(state: GeneralAgentState):
    """
    일반 대화 작업을 처리하는 작업자 함수입니다.
    """
    messages = state["messages"]
    response = llm.invoke(
        messages
        + [{"role": "system", "content": "당신은 일반적인 대화를 담당하는 챗봇입니다."}]
    )
    state["messages"] = [response]
    state["next"] = "supervisor"
    return state


# 그래프 구성
builder = StateGraph(GeneralAgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("VACATION_REQUEST", vacation_info_collector)
builder.add_node("vacation_info_extractor", vacation_info_extractor)
builder.add_node("vacation_confirmer", vacation_confirmer)
builder.add_node("vacation_submitter", vacation_submitter)
builder.add_node("GENERAL_CHAT", general_chat_agent)

builder.set_entry_point("supervisor")
builder.add_conditional_edges(
    "supervisor",
    lambda state: state["next"],
    {
        "VACATION_REQUEST": "VACATION_REQUEST",
        "GENERAL_CHAT": "GENERAL_CHAT",
        END: END,
    },
)

# 연차 신청 프로세스 흐름
builder.add_edge("VACATION_REQUEST", "vacation_info_extractor")
builder.add_edge("vacation_info_extractor", "vacation_confirmer")
builder.add_edge("vacation_confirmer", "vacation_submitter")
builder.add_edge("vacation_submitter", "supervisor")
builder.add_edge("GENERAL_CHAT", "supervisor")

checkpointer = MemorySaver()
# 그래프 컴파일 및 체크포인터 설정
graph = builder.compile(checkpointer=checkpointer)


# 일반 챗봇 및 연차 신청 처리 함수
def process_general_chat(message: str, session_state: GeneralAgentState) -> Dict:
    """
    일반 채팅 처리를 위한 함수

    Args:
        message: 사용자 메시지
        session_state: 기존 세션 상태 (없으면 새로 생성)

    Returns:
        Dict: 응답 및 세션 상태를 포함한 딕셔너리
    """
    logger.info(f"process_general_chat 시작: message={message}")

    # OpenAI API 키 확인
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다")
        return {
            "response": "설정 오류: OpenAI API 키가 설정되지 않았습니다.",
            "session_state": session_state or {},
        }

    global llm, graph, initialized_sessions

    # LLM 초기화
    if llm is None:
        logger.info("LLM 초기화")
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=OPENAI_API_KEY,
        )

    try:
        # 이 함수는 session_state에 thread_id가 있다고 가정함
        # main.py에서 전달된 session_id가 thread_id로 사용되어야 함
        thread_id = session_state.get("thread_id", "")
        logger.info(f"사용 중인 thread_id: {thread_id}")

        # 세션 초기화 필요 또는 빈 세션 확인
        needs_reset = initialized_sessions.get(thread_id) == False

        if needs_reset or not session_state.get("messages"):
            logger.info(f"새 세션 시작: thread_id={thread_id}")

            # 완전히 새로운 세션 상태 생성
            session_state = {
                "messages": [HumanMessage(content=message)] if message else [],
                "vacation_info": {"drafterId": "01180001", "mstPid": 1},
                "thread_id": thread_id,
                "interrupted": False,
            }

        else:
            # 기존 세션 계속 사용 - 새 메시지 추가
            if message:
                session_state["messages"].append(HumanMessage(content=message))

        # 그래프 실행 설정
        config = RunnableConfig(
            recursion_limit=10,
            configurable={
                "thread_id": thread_id,
                "interrupt_before_return": True,
                "initial_state": session_state,
            },
            tags=["vacation-request"],
        )

        # 상태 이력(체크포인트) 조회 - 디버깅용
        # 그래프 실행 - 스트리밍 모드로 진행
        events = []
        final_checkpoint = None

        # 2. 원하는 값으로 상태 업데이트
        graph.update_state(config, session_state)

        # Command 객체 생성 - 사용자 입력을 resume 값으로 전달
        resume_command = Command(resume=message)

        # 스트리밍으로 그래프 실행 재개
        for event in graph.stream(
            resume_command,
            config=config,
            stream_mode="values",
            interrupt_after="GENERAL_CHAT",
        ):
            events.append(event)
            final_checkpoint = event

        # 최종 상태 결정
        # - 그래프 실행이 끝났다면 final_checkpoint가 있을 것이고
        # - 그래프 실행이 아예 없었다면 session_state(딕셔너리) 자체를 결과로 반환
        result = final_checkpoint if final_checkpoint else session_state

        # 응답 메시지 추출
        response_text = ""
        if isinstance(result, dict):
            # 결과가 딕셔너리 형태라면 messages 키가 있는지 확인
            if "messages" in result and len(result["messages"]) > 0:
                response_text = result["messages"][-1].content

            # 세션 상태 업데이트
            session_state.update(result)

            # thread_id 유지 - main.py에서 받은 값 유지
            session_state["thread_id"] = thread_id

        elif hasattr(result, "values") and isinstance(result.values, dict):
            # final_checkpoint가 Checkpoint 형태라면
            if "messages" in result.values and len(result.values["messages"]) > 0:
                response_text = result.values["messages"][-1].content

            # 세션 상태 업데이트
            session_state.update(result.values)

            # thread_id 유지
            session_state["thread_id"] = thread_id

        # END 노드 도달 확인
        if session_state.get("next") == "__end__":
            logger.info(f"그래프 실행 완료: thread_id={thread_id} - 세션 초기화 진행")

            # 새 스레드 ID 생성
            new_thread_id = str(uuid.uuid4())
            logger.info(f"새 스레드 ID 생성: {new_thread_id}")

            # 초기화 상태 관리 - 기존 스레드 ID 삭제
            if thread_id in initialized_sessions:
                del initialized_sessions[thread_id]
                logger.info(f"기존 thread_id({thread_id})의 초기화 상태 삭제")

            # 새 세션 상태 생성 - thread_id를 새 값으로 설정
            new_session_state = {
                "messages": [],
                "vacation_info": {
                    "drafterId": "01180001",
                    "mstPid": 1,
                    "aprvNm": "",
                    "docCn": "",
                    "dayList": [],
                    "lineList": [],
                },
                "next": "supervisor",
                "interrupted": False,
                "thread_id": new_thread_id,  # 새 스레드 ID 설정
            }

            # 새 스레드 초기화 상태 설정
            initialized_sessions[new_thread_id] = False

            return {
                "response": response_text,
                "session_state": new_session_state,
                "metadata": {"thread_id": new_thread_id, "session_reset": True},
            }

        # 일반적인 응답 반환
        return {
            "response": response_text,
            "session_state": session_state,
            "metadata": {
                "thread_id": thread_id,
            },
        }

    except Exception as e:
        logger.error(f"챗봇 처리 중 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "response": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
            "session_state": session_state or {},
            "metadata": {"error": str(e)},
        }
