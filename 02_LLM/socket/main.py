from fastapi import (
    FastAPI,
    WebSocket,
    Form,
    Request,
    Response,
    WebSocketDisconnect,
    HTTPException,
)
from typing import List, Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import os
import uvicorn
from models import User, SessionLocal
import uuid
from passlib.hash import bcrypt
import logging

# Load environment variables once, at the start of the script.
load_dotenv()

# Initialize API keys and clients.
api_key = os.getenv("OPENAI_API_KEY")
sync_openai_client = OpenAI(api_key=api_key)
async_openai_client = AsyncOpenAI(api_key=api_key)

app = FastAPI()
# html파일을 서비스할 수 있는 jinja설정 (/templates 폴더사용)
templates = Jinja2Templates(directory="templates")

# Use a list to store chat responses. Consider using a more scalable storage solution for production.
chat_responses: List[str] = []

# Initialize a chat log with a system message.
chat_log = [
    {
        "role": "system",
        "content": (
            "You are a Helpful assistant, skilled in explaining complex concepts in simple terms. "
        ),
    }
]

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve the chat page."""
    return templates.TemplateResponse(
        "home.html", {"request": request, "chat_responses": chat_responses}
    )


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    """Handle user input from the chat form."""
    chat_log.append({"role": "user", "content": user_input})
    chat_responses.append(user_input)

    response = sync_openai_client.chat.completions.create(
        model="gpt-3.5-turbo", messages=chat_log, temperature=0.6
    )

    bot_response = response.choices[0].message.content
    chat_log.append({"role": "assistant", "content": bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse(
        "home.html", {"request": request, "chat_responses": chat_responses}
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket endpoint for real-time AI responses."""
    await websocket.accept()
    while True:
        user_message = await websocket.receive_text()
        async for ai_response in get_ai_response(user_message):
            await websocket.send_text(ai_response)


async def get_ai_response(message: str):
    """Generate responses from the AI asynchronously."""
    response = await async_openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant, skilled in explaining complex concepts in simple terms.",
            },
            {"role": "user", "content": message},
        ],
        stream=True,
    )

    async for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content


@app.post("/user/register")
async def register_user(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    nickname: Annotated[str, Form()],
):
    db = SessionLocal()
    try:
        logger.info(f"회원가입 시도 - 닉네임: {nickname}, 사용자명: {username}")

        # 사용자명 중복 체크
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.warning(f"회원가입 실패 - 중복된 사용자명: {username}")
            return JSONResponse(
                status_code=409, content={"detail": "이미 사용 중인 사용자명입니다."}
            )

        # 새 사용자 생성
        hashed_password = bcrypt.hash(password)
        new_user = User(
            id=str(uuid.uuid4()),
            username=username,
            password=hashed_password,
            nickname=nickname,
            is_admin=False,
        )

        logger.info(f"새 사용자 생성 - ID: {new_user.id}")

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"사용자 저장 완료 - ID: {new_user.id}")

        return {
            "user_id": new_user.id,
            "nickname": new_user.nickname,
            "is_admin": new_user.is_admin,
        }

    except Exception as e:
        logger.error(f"회원가입 오류: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post("/user/login")
async def login_user(
    username: Annotated[str, Form()], password: Annotated[str, Form()]
):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not bcrypt.verify(password, user.password):
            raise HTTPException(
                status_code=401, detail="잘못된 사용자명 또는 비밀번호입니다."
            )

        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "is_admin": user.is_admin,
        }

    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)
