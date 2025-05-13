"""
일반 챗봇 애플리케이션

이 애플리케이션은 일반 챗봇 인터페이스를 제공하며 연차 신청 기능을 내장하고 있습니다.
"""

import os
import json
import uuid
import logging
import traceback
import sys
from typing import Dict, Optional, List, Union
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 일반 챗봇 모듈 가져오기
from general_chatbot import process_general_chat

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("main_debug.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("main")

# 환경 변수 로드
load_dotenv()
API_BASE_URL = os.getenv("BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper")
logger.info(f"API_BASE_URL: {API_BASE_URL}")

# OpenAI API 키 확인
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
else:
    logger.info(f"OPENAI_API_KEY가 로드됨: 길이 {len(openai_api_key)}")
    logger.debug(f"API 키 처음 10자: {openai_api_key[:10]}...")

# API 키를 환경변수로 명시적 설정
os.environ["OPENAI_API_KEY"] = openai_api_key

# 세션 저장소
general_sessions: Dict[str, Dict] = {}  # 일반 챗봇 세션 추가

# FastAPI 앱 생성
app = FastAPI(title="N2 GW 일반 챗봇")

# 정적 파일 및 템플릿 설정
static_dir = Path(__file__).parent / "static"
templates_dir = Path(__file__).parent / "templates"
logger.info(f"정적 파일 디렉토리: {static_dir}")
logger.info(f"템플릿 디렉토리: {templates_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


# API 요청 모델
class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지")
    session_id: Optional[str] = None
    session_state: Optional[Dict] = None  # 세션 상태 추가
    agent_type: Optional[str] = Field(
        default="general", description="에이전트 유형 (general, api, vacation)"
    )


# 세션 ID 생성 및 검증
def get_or_create_session_id(session_id: Optional[str] = None) -> str:
    """세션 ID를 생성하거나 검증합니다."""
    logger.debug(f"세션 ID 검증/생성: session_id={session_id}")

    # 세션 ID가 제공되었으면 그대로 사용 (존재 여부와 상관없이)
    if session_id:
        logger.info(f"클라이언트에서 제공한 세션 ID 사용: {session_id}")
        return session_id

    # 세션 ID가 없는 경우만 새로 생성
    session_id = str(uuid.uuid4())
    logger.info(f"새 세션 ID 생성됨: {session_id}")

    return session_id


# 메인 페이지 - 일반 챗봇으로 리디렉션
@app.get("/", response_class=RedirectResponse)
def home():
    """메인 페이지 (N2 챗봇으로 리디렉션)"""
    logger.info("메인 페이지 요청 - N2 챗봇으로 리디렉션")
    return RedirectResponse(url="/general")


# N2 챗봇 페이지
@app.get("/general", response_class=HTMLResponse)
def general_chatbot_page(request: Request):
    """N2 챗봇 페이지"""
    logger.info("N2 챗봇 페이지 요청")
    return templates.TemplateResponse("general_chatbot.html", {"request": request})


# 채팅 API 엔드포인트
@app.post("/api/chat")
def chat(request: ChatRequest):
    """채팅 API 엔드포인트"""
    logger.info(f"채팅 API 요청 받음: message={request.message}")

    try:
        # 세션 ID 생성 또는 검증
        session_id = get_or_create_session_id(request.session_id)
        logger.debug(f"사용할 세션 ID: {session_id}")

        # 에이전트 유형에 따라 처리
        agent_type = request.agent_type or "general"

        if agent_type == "general":
            # N2 챗봇 요청 처리
            logger.info("N2 챗봇 요청 처리")
            result = process_general_agent_request(
                request.message, session_id, request.session_state
            )

            # session_id가 변경되었는지 확인
            if result.get("session_id") != session_id:
                logger.warning(
                    f"결과의 session_id가 변경됨: {result.get('session_id')} -> {session_id}"
                )
                result["session_id"] = session_id

            # session_state에 thread_id가 session_id와 일치하는지 확인
            if result.get("session_state", {}).get("thread_id") != session_id:
                logger.warning(
                    f"session_state의 thread_id 불일치: {result.get('session_state', {}).get('thread_id')} != {session_id}"
                )
                if "session_state" in result:
                    result["session_state"]["thread_id"] = session_id
        else:
            # 지원하지 않는 에이전트 유형
            logger.warning(f"지원하지 않는 에이전트 유형: {agent_type}")
            result = {
                "response": f"죄송합니다. 지원하지 않는 에이전트 유형입니다: {agent_type}",
                "session_id": session_id,
                "metadata": {"error": f"지원하지 않는 에이전트 유형: {agent_type}"},
            }

        logger.info("채팅 API 요청 처리 완료")
        return result
    except HTTPException as e:
        # HTTP 예외는 그대로 전달
        logger.error(f"HTTP 예외: {e.status_code} - {e.detail}")
        raise e
    except Exception as e:
        # 다른 모든 예외는 500 오류로 처리
        error_msg = f"채팅 API 처리 중 오류: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())

        # 클라이언트에게 응답할 오류 메시지 생성
        error_detail = {
            "message": "서버 내부 오류가 발생했습니다.",
            "error_type": type(e).__name__,
            "error_details": str(e),
        }

        raise HTTPException(status_code=500, detail=json.dumps(error_detail))


# N2 챗봇 요청 처리
def process_general_agent_request(
    message: str, session_id: str, session_state: Dict = None
):
    """N2 챗봇 요청 처리"""
    logger.info(f"N2 챗봇 요청 처리 시작: message={message}, session_id={session_id}")

    try:
        # 세션 상태 처리 로직
        if session_state:
            # 클라이언트에서 전달한 세션 상태 사용
            logger.debug("클라이언트에서 전달한 세션 상태 사용")

            # 중요: session_id를 thread_id로 설정
            session_state["thread_id"] = session_id
            logger.info(f"세션 상태에 thread_id 설정: {session_id}")

            # 필수 필드가 없는 경우 초기화
            if "messages" not in session_state:
                session_state["messages"] = []
                logger.info("session_state에 messages 필드 초기화")

            if "vacation_info" not in session_state:
                session_state["vacation_info"] = {
                    "drafterId": "01180001",  # 기본 직원 ID
                    "mstPid": 1,
                    "aprvNm": "",
                    "docCn": "",
                    "dayList": [],
                    "lineList": [],
                }
                logger.info("session_state에 vacation_info 필드 초기화")

            if "next" not in session_state:
                session_state["next"] = "supervisor"
                logger.info("session_state에 next 필드 초기화")

            if "interrupted" not in session_state:
                session_state["interrupted"] = False
                logger.info("session_state에 interrupted 필드 초기화")
        else:
            # 기존 서버 세션 상태 가져오기
            session_state = general_sessions.get(session_id, None)
            logger.debug(
                f"서버에 저장된 세션 상태 존재 여부: {session_state is not None}"
            )

            # 세션 상태가 없으면 새로 생성하고 thread_id 설정
            if not session_state:
                # GeneralAgentState와 동일한 구조로 초기화
                session_state = {
                    "messages": [],  # 메시지 배열 초기화
                    "vacation_info": {
                        "drafterId": "01180001",  # 기본 직원 ID
                        "mstPid": 1,
                        "aprvNm": "",
                        "docCn": "",
                        "dayList": [],
                        "lineList": [],
                    },
                    "next": "supervisor",  # 초기 노드
                    "interrupted": False,  # 인터럽트 상태
                }
                logger.info("새 세션 상태를 GeneralAgentState 구조로 초기화")

            # 기존 세션이든 새 세션이든 thread_id 설정
            session_state["thread_id"] = session_id
            logger.info(f"세션 상태에 thread_id 설정: {session_id}")

        # 챗봇 호출
        logger.info("process_general_chat 호출")
        result = process_general_chat(message, session_state)
        logger.debug(f"process_general_chat 처리 결과: {result}")

        if "session_state" in result:
            # thread_id 일관성 확인 및 설정
            if result["session_state"].get("thread_id") != session_id:
                logger.warning(
                    f"thread_id 불일치 감지: {result['session_state'].get('thread_id')} != {session_id}"
                )
                result["session_state"]["thread_id"] = session_id
                logger.info(f"thread_id 강제 일치 처리: {session_id}")

            # 세션 상태 업데이트 - 결과의 상태를 서버 세션 저장소에 저장
            general_sessions[session_id] = result["session_state"]
            logger.info("세션 상태 업데이트 완료")

            # 응답 반환
            logger.info("N2 챗봇 요청 처리 완료")

            # 그래프 실행이 완료되었는지 확인 (END 노드에 도달했는지)
            if result["session_state"].get("next") == "__end__":
                logger.info(
                    f"그래프 실행 완료: thread_id={session_id} - 세션 초기화 진행"
                )

                # 기존 세션 삭제
                if session_id in general_sessions:
                    del general_sessions[session_id]
                    logger.info(f"기존 세션 삭제: {session_id}")

                # 새 세션 ID 생성
                new_session_id = str(uuid.uuid4())
                logger.info(f"새 세션 ID 생성: {new_session_id}")

                # 새 빈 세션 상태 생성
                general_sessions[new_session_id] = {
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
                    "thread_id": new_session_id,
                }

                # 응답에 새 세션 ID 포함
                return {
                    "response": result["response"],
                    "session_id": new_session_id,  # 새 세션 ID 반환
                    "session_state": general_sessions[
                        new_session_id
                    ],  # 새 세션 상태 반환
                    "metadata": {"thread_id": new_session_id, "session_reset": True},
                }

            # 일반적인 경우 기존 세션 ID 유지
            return {
                "response": result["response"],
                "session_id": session_id,
                "session_state": result["session_state"],  # 세션 상태 반환
                "metadata": result.get("metadata", {}),
            }
        else:
            error_msg = "응답에 'session_state'가 없습니다."
            logger.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        error_msg = f"N2 챗봇 요청 처리 중 오류: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise Exception(error_msg)


# API 상태 확인
@app.get("/api/health")
def health_check():
    """API 상태 확인"""
    return {
        "status": "online",
        "api_base_url": API_BASE_URL,
        "openai_api_key": "configured" if openai_api_key else "not_configured",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("애플리케이션 시작 준비")

    # templates 및 static 디렉토리가 없으면 생성
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)
    logger.info("디렉토리 생성 완료")

    logger.info("서버 시작!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
