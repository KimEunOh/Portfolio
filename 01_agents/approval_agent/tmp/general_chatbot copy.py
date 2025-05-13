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
from typing import Dict, List, Any, TypedDict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from enum import Enum
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_function
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
import httpx

# ------------------------------------------------------
# 1. 기본 설정
# ------------------------------------------------------

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("general_chatbot_debug.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("general_chatbot")

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper")

# LLM 초기화를 위한 전역 변수
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
general_graph = None


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


# 에이전트 상태 정의
class GeneralAgentState(TypedDict):
    collection_initialized: bool
    messages: list
    vacation_info: DocumentInfo
    next: str


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
        self.client = httpx.AsyncClient(timeout=30)

    async def call_api(self, endpoint: str, method: str, params: Dict = None) -> Dict:
        """API 호출 함수"""
        logger.info(f"API 호출 시작: {method} {endpoint}")
        logger.debug(f"API 파라미터: {params}")

        try:
            url = f"{self.api_url}/{endpoint}"
            logger.debug(f"완전한 URL: {url}")

            headers = {"Content-Type": "application/json"}

            if method.upper() == "GET":
                response = await self.client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=params, headers=headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=params, headers=headers)
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
async def fetch_employee_info(drafterId: str) -> Dict:
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


async def fetch_remaining_vacation_days(drafterId: str) -> Dict:
    """직원의 잔여 연차 일수를 직접 API로 조회합니다."""
    logger.info(f"잔여 연차 조회: drafterId={drafterId}")
    try:
        endpoint = "remainder"
        method = "POST"
        params = {"drafterId": drafterId}

        result = await api_client.call_api(endpoint, method, params)

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


async def fetch_approval_line(drafterId: str) -> Dict:
    """직원의 결재 라인을 직접 API로 조회합니다."""
    logger.info(f"결재 라인 조회: drafterId={drafterId}")
    try:
        endpoint = "myLine"
        method = "POST"
        params = {"mstPid": 1, "drafterId": drafterId}

        result = await api_client.call_api(endpoint, method, params)

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


async def fetch_existing_vacations(drafterId: str) -> Dict:
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


async def submit_vacation_request_to_api(request_json: Dict) -> Dict:
    """연차 신청 요청을 API로 전송합니다."""
    logger.info(f"연차 신청 요청: {request_json}")
    try:
        endpoint = "register"
        method = "PUT"

        result = await api_client.call_api(endpoint, method, request_json)

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

    return day_list


# 제출 완료 후 카드 HTML 생성 함수
def create_vacation_card_html(
    document_info: DocumentInfo,
    employee_info: Dict,
    remaining_days: Any,
) -> Dict:
    """TypedDict 형식의 문서 정보에서 JSON 형태의 연차 정보를 생성합니다."""

    # 문서 정보에서 데이터 추출
    current_info = document_info.copy()
    remaining_days = current_info.get("remaining_days", 0)

    # 카드 HTML 생성 (스타일은 general_chatbot.html에 이미 정의되어 있음)
    card_html = f"""
    <div class="vacation-card">
        <h3>🗓️ 연차 신청 정보</h3>
        
        <div class="info-row">
            <div class="label">신청자</div>
            <div class="value">{employee_info.get('name', '홍길동')} {employee_info.get('position', '사원')}</div>
        </div>
        
        <div class="info-row">
            <div class="label">부서</div>
            <div class="value">{employee_info.get('department', '개발팀')}</div>
        </div>
        
        <div class="info-row">
            <div class="label">휴가 종류</div>
            <div class="value">{current_info.get('vacation_type', '연차')}</div>
        </div>
        
        <div class="info-row">
            <div class="label">기간</div>
            <div class="value">{current_info.get('reqYmd', '')}</div>
        </div>
        
        <div class="info-row">
            <div class="label">사유</div>
            <div class="value">{current_info.get('docCn', '')}</div>
        </div>
        
        <div class="approvers">
            <div class="label">결재자</div>
            <div>{current_info.get('lineList', [])}</div>
        </div>
        
        <div class="remain-days">
            남은 연차: {remaining_days}일
        </div>
    </div>
    """

    return card_html


async def create_vacation_request_json(
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
    system_prompt = """
    당신은 사용자 요청을 관리하는 Supervisor입니다. 
    다음 작업자들을 관리합니다: VACATION_REQUEST, GENERAL_CHAT

    VACATION_REQUEST : 사용자가 연차 신청작업과 관련된 내용을 입력할 때 호출합니다.
    GENERAL_CHAT : 사용자가 일반적인 내용을 입력할 때 호출합니다.

    주어진 사용자 메시지를 분석하고, 다음에 호출할 작업자를 결정하세요.
    각 작업자는 작업을 수행하고 결과와 상태를 반환합니다.
    모든 작업이 완료되면 FINISH를 반환합니다.
    """
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]

    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        return END

    return {"next": goto}


# 연차 정보 요청 및 파싱 노드
def vacation_agent(state: GeneralAgentState):
    """
    연차 신청 작업을 처리하는 작업자 함수입니다.
    """
    # 메시지 목록 가져오기
    messages = state["messages"]  # 마지막 메시지만 가져올지 고민

    # 초기 설정 (처음 실행 시에만)
    if not state["collection_initialized"]:
        employee_info = fetch_employee_info(state["vacation_info"]["drafterId"])
        remaining_days = fetch_remaining_vacation_days(
            state["vacation_info"]["drafterId"]
        )
        approval_line = fetch_approval_line(state["vacation_info"]["drafterId"])
        state["lineList"] = approval_line.get("data", [])
        state["collection_initialized"] = True

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

        # 첫 실행에서는 정보 입력 대기 상태로 반환
        return state

    user_input = interrupt("연차 신청 정보를 입력해주세요.")

    # 상태에 사용자 메시지 추가
    state["messages"].append(HumanMessage(content=user_input))

    # 기존 폼 상태 가져오기 (중요: 기존 상태 유지)
    current_form = state["vacation_info"].copy()

    # 모델을 사용해 입력에서 정보 추출
    extracted_info = llm.invoke(
        f"""사용자 입력: {user_input}
        다음 중 어떤 정보가 포함되어 있는지 추출하세요:
        - 연차 종류
        - 시작 날짜
        - 종료 날짜
        - 사유
        존재하는 정보만 추출하고, 없는 정보는 추출하지 마세요.
        JSON 형식으로 반환하세요.

        예시 :
        {
            "dvType": "연차",
            "start_date": "2024-04-20",
            "end_date": "2024-04-20",
            "docCn": "개인 사정"
        },
        {
            "dvType": "연차",
            "start_date": "2024-04-20",
            "end_date": "2024-04-20",
            "docCn": None
        }
        """
    )

    # JSON 파싱 (예시)
    import json

    try:
        new_info = json.loads(extracted_info)

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
            if value:  # 값이 있는 경우만 업데이트
                current_form[key] = value

    except (json.JSONDecodeError, Exception) as e:
        # 파싱 오류 시 메시지 전송
        logger.error(f"JSON 파싱 오류: {str(e)}")
        response = "입력하신 정보를 이해하지 못했습니다. 다시 명확하게 알려주세요."
        state["response"] = response
        state["messages"].append(AIMessage(content=response))
        state["vacation_info"] = current_form
        return state  # 같은 노드로 다시 돌아감

    # 업데이트된 정보 저장
    state["vacation_info"] = current_form

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
        state["response"] = f"다음 정보를 추가로 알려주세요:\n" + "\n".join(
            f"- {info}" for info in missing_fields
        )
        state["response"] = response
        state["messages"].append(AIMessage(content=response))
        return state  # 같은 노드로 다시 돌아감

    response = create_vacation_card_html(
        document_info=current_form,
        employee_info=employee_info,
        remaining_days=remaining_days,
    )

    state["response"] = response
    state["messages"].append(AIMessage(content=response))

    response = (
        f"다음 정보로 연차를 신청하시겠습니까?\n\n"
        f"확인하시면 '예'를, 수정하시려면 '아니오'를 입력해주세요."
    )

    state["response"] = response
    state["messages"].append(AIMessage(content=response))

    if "예" in user_input:
        # 연차 신청 처리
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
            return state  # 같은 노드로 다시 돌아감
        submit_vacation_request_to_api(state["vacation_info"])
        response = "연차 신청이 완료되었습니다."
        state["response"] = response
        state["messages"].append(AIMessage(content=response))
        return {"next": "supervisor"}
    else:
        response = "연차 신청을 취소하셨습니다."
        state["response"] = response
        state["messages"].append(AIMessage(content=response))
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
    return {"messages": [response]}


# 그래프 구성
builder = StateGraph(GeneralAgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_node("VACATION_REQUEST", vacation_agent)
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
builder.add_edge("VACATION_REQUEST", "supervisor")
builder.add_edge("GENERAL_CHAT", "supervisor")

# 그래프 컴파일
graph = builder.compile()


# 일반 챗봇 및 연차 신청 처리 함수
async def process_general_chat(message: str, session_state: Dict = None) -> Dict:
    """일반 챗봇 대화 처리 함수"""
    logger.info(f"process_general_chat 시작: message={message}")
    logger.debug(f"세션 상태: {session_state}")

    # OpenAI API 키 확인
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다")
        return {
            "response": "설정 오류: OpenAI API 키가 설정되지 않았습니다.",
            "session_state": session_state or {},
        }

    global llm, graph

    # LLM 초기화
    if llm is None:
        logger.info("LLM 초기화")
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=OPENAI_API_KEY,
        )

    try:
        # 세션 상태 초기화 또는 가져오기
        if not session_state:
            logger.info("새 세션 상태 생성")
            # 새 세션 생성
            session_state = {
                "messages": [HumanMessage(content=message)],
                "collection_initialized": False,
                "vacation_info": {
                    "drafterId": "01180001",  # 기본 직원 ID
                    "mstPid": 1,
                    "aprvNm": "",
                    "docCn": "",
                    "dayList": [],
                    "lineList": [],
                },
                "next": "supervisor",  # 초기 노드
            }
        else:
            # 기존 세션 상태 업데이트
            if "messages" not in session_state:
                session_state["messages"] = []
            session_state["messages"].append(HumanMessage(content=message))

        # 그래프 실행 설정
        config = {"recursion_limit": 25}

        # 그래프 실행
        logger.info("그래프 실행")
        result = graph.invoke(session_state, config=config)

        # 응답 추출
        response_text = ""
        if result["messages"] and len(result["messages"]) > 0:
            response_text = result["messages"][-1].content

        # 메타데이터 구성
        metadata = {}
        if "vacation_info" in result:
            metadata["vacation_info"] = result["vacation_info"]

        # 최종 응답
        return {
            "response": response_text,
            "session_state": result,
            "metadata": metadata,
        }

    except Exception as e:
        error_msg = f"챗봇 처리 중 오류: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())

        return {
            "response": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
            "session_state": session_state or {},
            "metadata": {"error": str(e), "error_trace": traceback.format_exc()},
        }
