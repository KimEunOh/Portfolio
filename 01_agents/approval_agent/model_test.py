import os
import json
import uuid  # 세션 ID 생성용
from openai import OpenAI
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing import Annotated, TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_teddynote.graphs import visualize_graph
from fastapi import FastAPI, HTTPException, Request, Cookie, Response, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig

# API 키 정보 로드
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# FastAPI 앱 생성
app = FastAPI()

# 세션 저장소 (메모리 기반)
sessions: Dict[str, Dict] = {}

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# State 정의 (missing_info 필드 추가)
class State(TypedDict):
    question: Annotated[List[str], add_messages]  # 메시지 히스토리
    extracted_date: Annotated[str, "vacation date"]  # 연차 날짜
    leave_type: Annotated[str, "vacation type"]  # 연차 종류 (예: 연차, 반차 등)
    reason: Annotated[str, "vacation reason"]  # 연차 사유
    name: Annotated[str, "User's name"]  # 신청자 이름
    missing_info: Annotated[bool, "missing information"]  # 부족한 정보 여부
    answer: Annotated[str, "Answer"]  # 사용자 입력에 대한 답변
    messages: Annotated[list, add_messages]  # 대화 기록
    waiting_for_input: Annotated[
        bool, "waiting for input"
    ]  # 사용자 입력 대기 상태 표시
    missing_field: Annotated[
        Optional[str], "missing field"
    ]  # 어떤 필드가 부족한지 표시


def extract_info(user_input: str) -> dict:
    prompt = f"""
        아래 대화 내용에서 연차 신청에 필요한 정보를 추출하여 반드시 아래 JSON 형식으로만 출력하시오.
        출력 형식 (다른 텍스트 없이 오직 JSON 형식만 출력):
        {{
            "extracted_date": "YYYY.MM.DD",  // 날짜 (입력에 날짜가 없으면 null)
            "leave_type": "연차",           // 연차 종류 (연차, 반차, 병가, 출장, 휴가 등; 입력이 없으면 null)
            "reason": "사유",              // 연차 사유 (입력이 없으면 null)
            "name": "신청자 이름"           // 신청자 이름 (입력이 없으면 null)
        }}

        대화 내용:
        {user_input}
    """

    response = llm.invoke([{"role": "user", "content": prompt}])
    result_str = response.content.strip()
    print("LLM Raw Response:", result_str)  # 디버깅용 출력

    # 마크다운 코드 블록 제거 (예: ```json ... ```)
    if result_str.startswith("```"):
        lines = result_str.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        result_str = "\n".join(lines).strip()

    try:
        extracted_data = json.loads(result_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM 응답을 JSON으로 파싱하지 못했습니다: {result_str}"
        ) from e

    return extracted_data


def chatbot(state: State) -> State:
    # 전체 대화 내용을 하나의 문자열로 결합
    all_messages = []
    if isinstance(state["question"], list):
        for msg in state["question"]:
            if isinstance(msg, dict):
                all_messages.append(msg.get("content", ""))
            else:
                all_messages.append(str(msg))
    else:
        all_messages.append(str(state["question"]))

    combined_input = " ".join(all_messages)

    # 전체 대화 내용에서 정보 추출
    extracted_data = extract_info(combined_input)

    # 각 필드를 명시적으로 업데이트 (기존 값은 덮어씀)
    updated_state = {}
    for key in ["extracted_date", "leave_type", "reason", "name"]:
        if extracted_data.get(key):  # 새로운 값이 있을 때만 업데이트
            updated_state[key] = extracted_data.get(key)
        else:
            # 기존 값 유지 또는 None 설정
            updated_state[key] = state.get(key)

    # 부족한 정보가 있는지 True/False로 체크하여 missing_info에 저장
    missing_fields = [
        key
        for key in ["extracted_date", "leave_type", "reason", "name"]
        if not updated_state.get(key)
    ]

    # 디버깅 출력 추가
    print(f"chatbot 함수 - missing_fields: {missing_fields}")
    print(f"chatbot 함수 - updated_state: {updated_state}")

    # 상태 업데이트 반환
    return {
        "messages": [{"role": "assistant", "content": "정보를 분석 중입니다..."}],
        "missing_info": bool(missing_fields),  # 명시적으로 이름 변경
        "waiting_for_input": False,  # 초기에는 입력 대기 상태가 아님
        **updated_state,
    }


def request_missing_info(state: State) -> State:
    prompts = {
        "extracted_date": "날짜를 입력해주세요. (예: 2025년 3월 17일)",
        "leave_type": "연차 종류를 입력해주세요. (연차, 반차, 병가 등)",
        "reason": "연차 사유를 입력해주세요.",
        "name": "이름을 입력해주세요.",
    }

    # 상태 확인 디버깅
    print(
        f"request_missing_info 함수 - 현재 상태: {state.get('missing_info')}, waiting: {state.get('waiting_for_input')}"
    )

    # 부족한 정보 확인
    for key, prompt in prompts.items():
        if not state.get(key):
            print(f"request_missing_info 함수 - 부족한 정보 발견: {key}")
            # 부족한 정보가 있으면 해당 프롬프트를 반환하고 사용자 입력을 기다림
            return {
                "messages": [{"role": "assistant", "content": prompt}],
                "missing_info": True,
                "waiting_for_input": True,  # 사용자 입력 대기 상태 표시
                "missing_field": key,  # 어떤 필드가 부족한지 표시
                **{
                    k: state.get(k)
                    for k in ["extracted_date", "leave_type", "reason", "name"]
                },
            }

    print("request_missing_info 함수 - 모든 정보가 있음")
    # 모든 정보가 있으면 다음 단계로 진행
    return {
        "messages": [],
        "missing_info": False,
        "waiting_for_input": False,
        **{k: state.get(k) for k in ["extracted_date", "leave_type", "reason", "name"]},
    }


def update_missing_info(state: State) -> State:
    if not state.get("waiting_for_input"):
        return state

    # 사용자의 마지막 입력 가져오기
    last_message = None
    if isinstance(state["question"], list):
        messages = [
            msg.get("content", "") if isinstance(msg, dict) else str(msg)
            for msg in state["question"]
        ]
        last_message = messages[-1] if messages else None
    else:
        last_message = str(state["question"])

    if not last_message:
        return state

    # 마지막 메시지에서 정보 추출
    extracted_data = extract_info(last_message)

    # 현재 부족한 필드에 대한 정보만 업데이트
    missing_field = state.get("missing_field")
    if missing_field and extracted_data.get(missing_field):
        updated_state = {
            k: state[k] for k in ["extracted_date", "leave_type", "reason", "name"]
        }
        updated_state[missing_field] = extracted_data[missing_field]

        # 업데이트 확인 메시지 생성
        field_names = {
            "extracted_date": "날짜",
            "leave_type": "연차 종류",
            "reason": "사유",
            "name": "이름",
        }
        update_message = f"{field_names.get(missing_field, missing_field)}이(가) 업데이트되었습니다: {extracted_data[missing_field]}"

        return {
            "messages": [{"role": "assistant", "content": update_message}],
            "missing_info": True,  # 다른 정보가 더 필요할 수 있으므로 True로 유지
            "waiting_for_input": False,  # 입력 처리 완료
            **updated_state,
        }
    else:
        # 필요한 정보를 얻지 못한 경우
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"죄송합니다. 입력하신 내용에서 필요한 정보를 찾지 못했습니다. 다시 한 번 입력해주세요.",
                }
            ],
            "missing_info": True,
            "waiting_for_input": True,
            "missing_field": missing_field,
            **{k: state[k] for k in ["extracted_date", "leave_type", "reason", "name"]},
        }


def response_bot(state: State) -> State:
    # 현재 상태의 모든 정보를 포함한 응답 생성
    response_text = (
        f"연차 신청 정보를 확인해드리겠습니다:\n\n"
        f"신청자: {state.get('name', '미입력')}\n"
        f"날짜: {state.get('extracted_date', '미입력')}\n"
        f"종류: {state.get('leave_type', '미입력')}\n"
        f"사유: {state.get('reason', '미입력')}"
    )

    # 상태 업데이트 반환
    return {
        "answer": response_text,
        "messages": [{"role": "assistant", "content": response_text}],
        **{
            k: state[k]
            for k in ["extracted_date", "leave_type", "reason", "name", "missing_info"]
        },
    }


# 조건부 엣지 함수 수정: missing_info 상태와 waiting_for_input 상태를 모두 고려
def missing_info(state: State) -> str:
    waiting = state.get("waiting_for_input", False)
    missing = state.get("missing_info", False)

    print(f"missing_info 함수 - 상태 확인: waiting={waiting}, missing={missing}")

    # 대기 상태일 때는 업데이트 노드로 전달
    if waiting:
        print("missing_info 함수: update_missing_info 반환 (대기 상태)")
        return "update_missing_info"

    # 부족한 정보가 있지만 대기 상태가 아니면 request_missing_info로
    elif missing:
        print("missing_info 함수: request_missing_info 반환 (부족한 정보)")
        return "request_missing_info"

    # 모든 정보가 있으면 응답 생성
    else:
        print("missing_info 함수: response_bot 반환 (모든 정보 있음)")
        return "response_bot"


# 그래프 구조 재구성
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)  # 사용자 입력 분석
graph_builder.add_node("request_missing_info", request_missing_info)  # 부족한 정보 질문
graph_builder.add_node("update_missing_info", update_missing_info)  # 사용자 응답 반영
graph_builder.add_node("response_bot", response_bot)  # 최종 응답 생성

# 시작 노드에서 chatbot으로
graph_builder.add_edge(START, "chatbot")

# chatbot에서 missing_info 함수에 따라 분기
graph_builder.add_conditional_edges(
    "chatbot",
    missing_info,
    {
        "request_missing_info": "request_missing_info",
        "update_missing_info": "update_missing_info",
        "response_bot": "response_bot",
    },
)

# request_missing_info에서는 바로 종료 (사용자 입력 대기)
graph_builder.add_edge("request_missing_info", END)

# update_missing_info에서 missing_info 함수에 따라 분기
graph_builder.add_conditional_edges(
    "update_missing_info",
    missing_info,
    {
        "request_missing_info": "request_missing_info",
        "update_missing_info": "update_missing_info",
        "response_bot": "response_bot",
    },
)

# response_bot에서는 종료
graph_builder.add_edge("response_bot", END)

graph = graph_builder.compile()


# 백엔드로부터 question 값을 받을 요청 모델
class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # 세션 ID 필드 추가


# 세션 ID 생성 및 검증
def get_or_create_session_id(
    session_id: Optional[str] = Cookie(None), response: Response = None
) -> str:
    if not session_id or session_id not in sessions:
        session_id = str(uuid.uuid4())
        if response:
            response.set_cookie(key="session_id", value=session_id, httponly=True)
    return session_id


@app.post("/api/v1/ask")
def ask_chatbot(request: ChatRequest, response: Response):
    try:
        # 세션 ID 확인 또는 생성
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(key="session_id", value=session_id, httponly=True)

        print(f"요청 처리 중: session_id={session_id}, question={request.question}")

        # 세션 상태 확인 또는 초기화
        if session_id in sessions:
            # 기존 세션 상태 로드
            print(f"기존 세션 사용: {session_id}")
            previous_state = sessions[session_id]["state"]
            previous_messages = sessions[session_id]["messages"]

            # 사용자 질문 추가
            user_msg = {"role": "user", "content": request.question}
            if not previous_state.get("question"):
                previous_state["question"] = [user_msg]
            else:
                previous_state["question"].append(user_msg)

            # 초기 상태는 이전 상태를 기반으로 설정
            initial_state = previous_state

            print(f"기존 세션 상태: {initial_state}")
        else:
            # 새 세션 초기화
            print(f"새 세션 생성: {session_id}")
            initial_state = {
                "question": [{"role": "user", "content": request.question}],
                "messages": [],  # 빈 메시지 배열로 시작
                "extracted_date": None,
                "leave_type": None,
                "reason": None,
                "name": None,
                "missing_info": None,  # 명시적으로 None 설정
                "answer": None,
                "waiting_for_input": False,  # 초기에는 입력 대기 상태가 아님
                "missing_field": None,
            }
            sessions[session_id] = {"state": initial_state.copy(), "messages": []}

        print(f"초기 상태 설정: {initial_state}")

        config = RunnableConfig(recursion_limit=25)
        messages = []  # 현재 실행에서 생성된 메시지를 저장할 리스트
        last_event = None

        # 그래프 실행
        print(f"그래프 실행 시작: {request.question}")
        for i, event in enumerate(graph.stream(initial_state, config=config)):
            # 모든 이벤트에 대한 디버깅 출력
            print(
                f"Event #{i+1} 발생:",
                {
                    k: v
                    for k, v in event.items()
                    if k in ["waiting_for_input", "missing_info", "missing_field"]
                },
            )

            # 이벤트의 모든 필드 출력
            print(
                f"Event #{i+1} 전체 상태:",
                {k: v for k, v in event.items() if k != "messages"},
            )

            # 중첩된 메시지 구조 처리
            event_messages = []

            # 각 노드에서 생성된 메시지 추출
            for node_name, node_state in event.items():
                if isinstance(node_state, dict) and "messages" in node_state:
                    for msg in node_state["messages"]:
                        if (
                            isinstance(msg, dict)
                            and msg.get("role")
                            and msg.get("content")
                        ):
                            event_messages.append(msg)

            # 새로운 메시지만 추가
            for msg in event_messages:
                if msg not in messages:
                    messages.append(msg)
                    print(f"메시지 추가: {msg}")

            last_event = event

        # 최종 응답 구성
        if not last_event:
            return {"status": "error", "message": "그래프 실행 중 오류가 발생했습니다."}

        # 중첩 구조에서 상태 필드 추출
        final_state = {}
        for node_name, node_data in last_event.items():
            if isinstance(node_data, dict):
                for field in [
                    "extracted_date",
                    "leave_type",
                    "reason",
                    "name",
                    "missing_info",
                    "waiting_for_input",
                ]:
                    if field in node_data and node_data[field] is not None:
                        final_state[field] = node_data[field]

        # 세션에 최종 상태와 누적된 메시지 저장
        if session_id in sessions:
            # 최종 상태 저장
            sessions[session_id]["state"] = final_state

            # 새 메시지 저장 (중복 방지)
            session_messages = sessions[session_id]["messages"]
            for msg in messages:
                if msg not in session_messages:
                    session_messages.append(msg)
        else:
            sessions[session_id] = {"state": final_state, "messages": messages.copy()}

        print("최종 세션 상태:", sessions[session_id]["state"])
        print("세션 메시지:", sessions[session_id]["messages"])

        response = {
            "status": "success",
            "session_id": session_id,
            "messages": messages,  # 현재 실행에서 생성된 메시지만 반환
            "state": final_state,
        }

        return response

    except Exception as e:
        import traceback

        print(f"Error in ask_chatbot: {str(e)}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
