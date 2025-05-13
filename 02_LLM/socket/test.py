from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List
import base64
import asyncio
import datetime
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import ollama

# ----------- DB 설정 -----------
DATABASE_URL = "sqlite:///./sqlite.db"

# 스레드는 FastAPI와 같은 비동기 작업이 필요한 경우 사용
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# autocommit은 데이터 베이스 작업을 자동으로 커밋할지 여부 결정(영구적)
# autoflush는 데이터베이스에 데이터를 자동으로 플러시할지 여부 결정(비영구적)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

templates = Jinja2Templates(directory="templates")
Base = declarative_base()


# ---------- 테이블 모델 선언 ----------
class Room(Base):
    __tablename__ = "rooms"
    roomID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    roomName = Column(String, unique=True, index=True)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    senderID = Column(Integer, index=True)
    roomID = Column(Integer, index=True)
    msg = Column(String)
    ts = Column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    userID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userName = Column(String, unique=True, index=True)


# 실제 DB 테이블 생성 (이미 있을 경우 무시)
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def call_ollama(
    prompt: str,
    model: str = "hf.co/Bllossom/llama-3.2-Korean-Bllossom-3B-gguf-Q4_K_M",
    options: dict = None,
) -> str:
    """
    로컬 Ollama 모델에 프롬프트를 전송하고, 결과 텍스트를 반환합니다.
    :param prompt: 모델에 전송할 프롬프트 문자열
    :param model: 사용할 모델 이름 (기본값: 'hf.co/Bllossom/llama-3.2-Korean-Bllossom-3B-gguf-Q4_K_M')
    :param options: 모델 파라미터를 포함한 옵션 딕셔너리 (예: {'temperature': 0.7})
    :return: 모델의 응답 문자열
    """

    system_prompt = (
        "당신은 한국어에 능통하며, 사용자에게 친절하고 간결한 어조로 대답하는 AI 어시스턴트입니다. "
        "사용자가 묻는 모든 질문에 명확하고 사실적인 정보를 제공하십시오."
        "모든 응답은 한국어로만 작성되어야 합니다."
    )

    try:
        # 필요한 경우 system 프롬프트나 추가 사용자의 이전 메시지를 messages 리스트에 포함할 수도 있음
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        # ollama.chat() 호출
        # options에 {'temperature': 0.7, 'top_p': 0.9} 등 다양한 파라미터를 전달 가능
        response = ollama.chat(model=model, messages=messages, options=options)

        return response["message"]["content"].strip()

    except Exception:
        # 오류 발생 시 기본 답변
        return "죄송합니다. 답변을 생성할 수 없습니다."


# ------------------ FastAPI 앱 시작 -------------------
app = FastAPI()


# ------------------ 웹소켓 매니저 -------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: str):
        if room_id in self.active_connections:
            tasks = []
            for connection in self.active_connections[room_id]:
                tasks.append(connection.send_text(message))
            await asyncio.gather(*tasks)


manager = ConnectionManager()


# ------------------ 메시지 출력 모델 (pydantic) -------------------
class MessageOut(BaseModel):
    senderName: str
    msg: str
    ts: str  # 혹은 datetime 등


# ------------------ 라우터 -------------------
@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    """메인 페이지 반환"""
    return templates.TemplateResponse("test.html", {"request": request})


@app.get("/rooms/{room_name}/messages", response_model=List[MessageOut])
def get_room_messages(room_name: str, db: Session = Depends(get_db)):
    """
    특정 방의 과거 메시지 목록을 조회하는 엔드포인트.
    """
    room_obj = db.query(Room).filter_by(roomName=room_name).first()
    if not room_obj:
        return []

    msgs = (
        db.query(Message)
        .filter_by(roomID=room_obj.roomID)
        .order_by(Message.id.asc())
        .all()
    )

    results = []
    for m in msgs:
        user_obj = db.query(User).filter_by(userID=m.senderID).first()
        sender_name = user_obj.userName if user_obj else "Unknown"
        results.append(
            MessageOut(
                senderName=sender_name,
                msg=m.msg,
                ts=str(m.ts),
            )
        )
    return results


@app.websocket("/ws/{encoded_room_id}/{encoded_user_name}")
async def websocket_endpoint(
    websocket: WebSocket,
    encoded_room_id: str,
    encoded_user_name: str,
    db: Session = Depends(get_db),
):
    """
    room_id와 user_name을 Base64로 인코딩해서 받는다.
    디코딩 후 실제 방 ID와 사용자 이름으로 사용한다.
    """
    try:
        room_str = base64.b64decode(encoded_room_id.encode("utf-8")).decode("utf-8")
        user_str = base64.b64decode(encoded_user_name.encode("utf-8")).decode("utf-8")
    except Exception:
        room_str = "unknown_room"
        user_str = "unknown_user"

    # Room 생성 or 조회
    existing_room = db.query(Room).filter_by(roomName=room_str).first()
    if not existing_room:
        new_room = Room(roomName=room_str)
        db.add(new_room)
        db.commit()
        db.refresh(new_room)
        room_id = new_room.roomID
    else:
        room_id = existing_room.roomID

    # User 생성 or 조회
    existing_user = db.query(User).filter_by(userName=user_str).first()
    if not existing_user:
        new_user = User(userName=user_str)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user_id = new_user.userID
    else:
        user_id = existing_user.userID

    # "봇" 계정 생성 (기록용)
    bot_user = db.query(User).filter_by(userName="AI").first()
    if not bot_user:
        new_bot = User(userName="AI")
        db.add(new_bot)
        db.commit()
        db.refresh(new_bot)
        bot_user = new_bot

    # 웹소켓 연결
    await manager.connect(websocket, room_str)

    try:
        while True:
            data = await websocket.receive_text()

            # 메시지를 DB에 저장
            new_message = Message(senderID=user_id, roomID=room_id, msg=data)
            db.add(new_message)
            db.commit()
            db.refresh(new_message)  # 여기서 new_message.ts 값 확보

            # 브로드캐스트할 메시지: "유저이름: 내용"
            message = f"{user_str}||{new_message.ts.isoformat()}||{data}"
            await manager.broadcast(message, room_str)

            if "AI" in room_str and user_str != "AI":
                prompt = data  # 사용자의 최신 메시지를 프롬프트로 삼는다.
                bot_response = call_ollama(prompt)

                # 봇 메시지도 DB 저장
                bot_message = Message(
                    senderID=bot_user.userID, roomID=room_id, msg=bot_response
                )
                db.add(bot_message)
                db.commit()
                db.refresh(bot_message)

                # 브로드캐스트 (보낸 주체는 "봇")
                bot_broadcast_msg = f"AI||{bot_message.ts.isoformat()}||{bot_response}"
                await manager.broadcast(bot_broadcast_msg, room_str)

    except WebSocketDisconnect:
        # 연결 종료
        manager.disconnect(websocket, room_str)
        system_time = datetime.datetime.utcnow().isoformat()
        exit_msg = f"System||{system_time}||{user_str}님이 채팅을 종료하셨습니다."
        await manager.broadcast(exit_msg, room_str)
