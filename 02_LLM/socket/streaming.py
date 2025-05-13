from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Form,
    Depends,
    HTTPException,
    BackgroundTasks,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Set, Optional, Union
import json
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine, event
import asyncio
import aioredis
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import aiokafka
from functools import lru_cache
import weakref
import gc
from models import (
    User,
    Message,
    get_db,
    init_db,
    DB_FILE,
)
import hashlib
import os
import psutil
import time

# Redis 관련 전역 변수
REDIS_URL = "redis://localhost:6379/0"
redis_pool = None
REDIS_POOL_SIZE = 100

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Kafka 설정
USE_KAFKA = False
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "chat_messages"

# 데이터베이스 커넥션 풀 설정
DB_POOL_SIZE = 50
DB_MAX_OVERFLOW = DB_POOL_SIZE // 2
DB_POOL_TIMEOUT = 30

# 스레드 풀 설정
thread_pool = ThreadPoolExecutor(max_workers=4)

# 채팅방 정보
CHAT_ROOMS = {
    "room1": "일반 채팅방",
    "room2": "게임 채팅방",
    "room3": "음악 채팅방",
    "room4": "영화 채팅방",
}

# 상수 정의
MAX_CONNECTIONS_PER_ROOM = 100
WEBSOCKET_PING_INTERVAL = 30  # 30초
WEBSOCKET_PING_TIMEOUT = 5  # 5초
MESSAGE_QUEUE_SIZE = 1000  # 메시지 큐 최대 크기
BROADCAST_BATCH_SIZE = 100  # 브로드캐스트 배치 크기
CLEANUP_INTERVAL = 60  # 1분마다 정리
MAX_MESSAGES_PER_ROOM = 100  # 방당 최대 메시지 수
ERROR_COUNT_RESET_INTERVAL = 3600  # 1시간마다 에러 카운트 초기화

# Shard 관리
SHARD_COUNT = 10
current_shard = 0


# 데이터 모델
class UserInfo(BaseModel):
    id: str
    nickname: str
    is_admin: bool = False
    created_at: datetime = datetime.now()
    current_room: str = "room1"


class ChatMessage(BaseModel):
    user_id: str
    content: str
    type: str = "user"
    room_id: str
    timestamp: datetime = datetime.now()


# 연결 관리자
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, weakref.ref[WebSocket]]] = (
            defaultdict(dict)
        )
        self.connection_shards: List[Dict[str, Dict[str, weakref.ref[WebSocket]]]] = [
            defaultdict(dict) for _ in range(SHARD_COUNT)
        ]
        self.shard_queues: List[Dict[str, asyncio.Queue]] = [
            defaultdict(lambda: asyncio.Queue(maxsize=MESSAGE_QUEUE_SIZE))
            for _ in range(SHARD_COUNT)
        ]
        self.shard_processors: List[List[asyncio.Task]] = [
            [] for _ in range(SHARD_COUNT)
        ]
        self.shard_locks: List[asyncio.Lock] = [
            asyncio.Lock() for _ in range(SHARD_COUNT)
        ]
        self.user_info: Dict[str, UserInfo] = {}
        self.room_participants: Dict[str, Set[str]] = defaultdict(set)
        self.admin_messages: Dict[str, List[ChatMessage]] = defaultdict(list)
        self.user_current_room: Dict[str, str] = {}
        self.message_timestamps = {}
        self.error_counts = defaultdict(int)
        self.start_time = time.time()
        self.message_counts = defaultdict(int)
        self.last_message_time = defaultdict(float)
        self.producer = None
        self.consumer = None
        self.initialized = False
        self.message_processors = []
        self.connection_count = 0
        self.last_cleanup = time.time()
        self.last_error_reset = time.time()
        self.room_messages: Dict[str, List[dict]] = defaultdict(list)
        self.cleanup_task = None
        self.error_reset_task = None
        self.message_batch_size = 50  # 메시지 배치 크기
        self.batch_timeout = 0.1  # 배치 타임아웃 (초)
        self.connection_pools: Dict[str, List[WebSocket]] = defaultdict(list)  # 연결 풀
        self.last_broadcast_time: Dict[str, float] = defaultdict(
            float
        )  # 마지막 브로드캐스트 시간

    async def initialize(self):
        """비동기 초기화 및 정리 작업 시작"""
        if self.initialized:
            return

        print("Initializing ConnectionManager...")  # 디버깅 로그

        # 정리 작업 시작
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self.error_reset_task = asyncio.create_task(self._periodic_error_reset())

        # 각 채팅방에 대한 메시지 큐 처리기 시작
        for room_id in CHAT_ROOMS:
            print(f"Starting message queue processor for room {room_id}")  # 디버깅 로그
            self.message_processors.append(
                asyncio.create_task(self._process_message_queue(room_id))
            )

        self.initialized = True
        print("ConnectionManager initialized successfully")  # 디버깅 로그

    async def shutdown(self):
        """리소스 정리"""
        print("Shutting down ConnectionManager...")  # 디버깅 로그

        try:
            # cleanup_task 취소
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            # error_reset_task 취소
            if self.error_reset_task and not self.error_reset_task.done():
                self.error_reset_task.cancel()
                try:
                    await self.error_reset_task
                except asyncio.CancelledError:
                    pass

            # 메시지 프로세서 작업 취소
            for processor in self.message_processors:
                if not processor.done():
                    processor.cancel()
                    try:
                        await processor
                    except asyncio.CancelledError:
                        pass

            # 모든 WebSocket 연결 종료
            for room_id in list(self.active_connections.keys()):
                for user_id, ws_ref in list(self.active_connections[room_id].items()):
                    ws = ws_ref() if ws_ref else None
                    if ws and not getattr(ws, "_closed", False):
                        try:
                            await ws.close(code=1000, reason="Server shutdown")
                        except Exception as e:
                            print(f"Error closing WebSocket for user {user_id}: {e}")

            # 메시지 큐 정리
            for room_id in list(self.shard_queues):
                for shard_id in range(SHARD_COUNT):
                    self.shard_queues[shard_id][room_id] = asyncio.Queue(
                        maxsize=MESSAGE_QUEUE_SIZE
                    )

            # 연결 및 참가자 정보 초기화
            self.active_connections.clear()
            self.room_participants.clear()
            self.user_info.clear()
            self.error_counts.clear()

            print("ConnectionManager shutdown completed")  # 디버깅 로그

        except Exception as e:
            print(f"Error during ConnectionManager shutdown: {e}")
        finally:
            self.initialized = False

    @lru_cache(maxsize=1000)
    def get_user_info(self, user_id: str) -> Optional[UserInfo]:
        """사용자 정보 조회 (캐시 적용)"""
        return self.user_info.get(user_id)

    def _get_shard_id(self, user_id: str) -> int:
        """사용자 ID를 기반으로 샤드 ID 결정"""
        return hash(user_id) % SHARD_COUNT

    async def _process_shard_messages(self, shard_id: int, room_id: str):
        """샤드별 메시지 처리"""
        print(f"Starting shard processor for shard {shard_id}, room {room_id}")

        try:
            queue = self.shard_queues[shard_id][room_id]
            batch = []
            last_process_time = time.time()

            while True:
                try:
                    # 배치 처리를 위한 메시지 수집
                    while len(batch) < self.message_batch_size:
                        try:
                            message = await asyncio.wait_for(
                                queue.get(), timeout=self.batch_timeout
                            )
                            batch.append(message)
                        except asyncio.TimeoutError:
                            break

                    current_time = time.time()

                    # 배치가 있거나 일정 시간이 지난 경우 처리
                    if batch and (
                        len(batch) >= self.message_batch_size
                        or current_time - last_process_time >= self.batch_timeout
                    ):
                        async with self.shard_locks[shard_id]:
                            # 배치 메시지 브로드캐스트
                            if len(batch) == 1:
                                await self._broadcast_to_shard(
                                    shard_id,
                                    self.connection_shards[shard_id][room_id].items(),
                                    batch[0],
                                )
                            else:
                                await self._broadcast_to_shard(
                                    shard_id,
                                    self.connection_shards[shard_id][room_id].items(),
                                    batch,
                                )

                            # 메시지 히스토리 업데이트
                            for message in batch:
                                self._update_room_messages(room_id, message)

                        batch = []
                        last_process_time = current_time

                    # 처리 간격 조절
                    await asyncio.sleep(0.01)

                except Exception as e:
                    print(
                        f"Error processing messages in shard {shard_id}, room {room_id}: {e}"
                    )
                    batch = []  # 에러 발생 시 배치 초기화
                    await asyncio.sleep(1)  # 에러 발생 시 잠시 대기

        except Exception as e:
            print(f"Fatal error in shard processor {shard_id}, room {room_id}: {e}")
        finally:
            # 프로세서 종료 시 정리
            if shard_id < len(self.shard_processors):
                processors = self.shard_processors[shard_id]
                for i, processor in enumerate(processors):
                    if processor and processor.done():
                        processors[i] = None

    async def _process_message_queue(self, room_id: str):
        """메시지 큐 처리기 - 샤드 기반 처리"""
        print(f"Starting message queue processor for room {room_id}")

        while True:
            try:
                # 각 샤드에 대한 프로세서 시작
                for shard_id in range(SHARD_COUNT):
                    # 기존 프로세서가 없거나 완료된 경우에만 새로 시작
                    if (
                        shard_id >= len(self.shard_processors)
                        or not self.shard_processors[shard_id]
                        or all(
                            p is None or p.done()
                            for p in self.shard_processors[shard_id]
                        )
                    ):

                        processor = asyncio.create_task(
                            self._process_shard_messages(shard_id, room_id)
                        )

                        # 샤드 프로세서 목록 확장
                        while len(self.shard_processors) <= shard_id:
                            self.shard_processors.append([])

                        self.shard_processors[shard_id] = [processor]

                await asyncio.sleep(1)  # 주기적 점검 간격

            except Exception as e:
                print(f"Error in message queue processor for room {room_id}: {e}")
                await asyncio.sleep(1)  # 에러 발생 시 잠시 대기

    async def _broadcast_messages(self, room_id: str, messages: list):
        """최적화된 메시지 브로드캐스트"""
        try:
            current_time = time.time()
            # 브로드캐스트 속도 제어
            if (
                current_time - self.last_broadcast_time[room_id] < 0.01
            ):  # 최소 10ms 간격
                await asyncio.sleep(0.01)

            active_connections = []
            if room_id in self.active_connections:
                for user_id, ws_ref in list(self.active_connections[room_id].items()):
                    ws = ws_ref() if ws_ref else None
                    if ws and not getattr(ws, "_closed", False):
                        active_connections.append(ws)
                    else:
                        if user_id in self.active_connections[room_id]:
                            del self.active_connections[room_id][user_id]
                        self.room_participants[room_id].discard(user_id)

            if active_connections:
                # 메시지 전송을 병렬로 처리
                send_tasks = []
                for ws in active_connections:
                    if len(messages) == 1:
                        send_tasks.append(self._safe_send(ws, messages[0]))
                    else:
                        send_tasks.append(self._safe_send(ws, messages))

                # 병렬 전송 처리 (타임아웃 적용)
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*send_tasks, return_exceptions=True),
                        timeout=2.0,  # 2초 타임아웃
                    )
                except asyncio.TimeoutError:
                    print(f"Broadcast timeout in room {room_id}")

            # 메시지 히스토리 업데이트 (최적화)
            self._update_room_messages(room_id, messages)
            self.last_broadcast_time[room_id] = time.time()

        except Exception as e:
            print(f"Error in broadcast_messages for room {room_id}: {e}")

    async def _safe_send(self, websocket: WebSocket, data: Union[dict, list]):
        """안전한 WebSocket 메시지 전송"""
        try:
            await websocket.send_json(data)
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def _update_room_messages(self, room_id: str, messages: list):
        """메시지 히스토리 업데이트 (메모리 관리 최적화)"""
        try:
            # 배치로 메시지 추가 (최대 개수 제한)
            current_messages = self.room_messages[room_id]
            new_messages = messages if isinstance(messages, list) else [messages]

            # 메모리 효율을 위해 리스트 크기 관리
            if len(current_messages) + len(new_messages) > MAX_MESSAGES_PER_ROOM:
                # 오래된 메시지 제거
                self.room_messages[room_id] = (
                    current_messages[-(MAX_MESSAGES_PER_ROOM - len(new_messages)) :]
                    + new_messages
                )
            else:
                current_messages.extend(new_messages)

        except Exception as e:
            print(f"Error updating room messages: {e}")

    async def broadcast(self, message: dict, room_id: str):
        """메시지 브로드캐스트 (샤딩 적용)"""
        try:
            if "id" not in message:
                message["id"] = str(uuid.uuid4())
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
            if "room_id" not in message:
                message["room_id"] = room_id

            print(f"Broadcasting message to room {room_id}")  # 디버깅 로그

            # 샤드별로 연결을 그룹화
            shard_connections = defaultdict(list)
            if room_id in self.active_connections:
                for user_id, ws_ref in list(self.active_connections[room_id].items()):
                    ws = ws_ref() if ws_ref else None
                    if ws and not getattr(ws, "_closed", False):
                        shard_id = self._get_shard_id(user_id)
                        shard_connections[shard_id].append((user_id, ws))
                    else:
                        if user_id in self.active_connections[room_id]:
                            del self.active_connections[room_id][user_id]
                        self.room_participants[room_id].discard(user_id)

            # 샤드별로 병렬 처리
            broadcast_tasks = []
            for shard_id, connections in shard_connections.items():
                if connections:
                    task = asyncio.create_task(
                        self._broadcast_to_shard(shard_id, connections, message)
                    )
                    broadcast_tasks.append(task)

            if broadcast_tasks:
                await asyncio.gather(*broadcast_tasks)

            # 메시지 히스토리 업데이트
            self._update_room_messages(room_id, message)
            return True

        except Exception as e:
            print(f"Broadcasting error: {e}")
            return False

    async def _broadcast_to_shard(
        self, shard_id: int, connections: List[tuple], message: dict
    ):
        """샤드 내의 연결들에게 메시지 전송"""
        try:
            print(
                f"Broadcasting to shard {shard_id} with {len(connections)} connections"
            )
            send_tasks = []

            # 샤드 내에서 배치 처리
            batch_size = 50  # 한 번에 처리할 연결 수
            for i in range(0, len(connections), batch_size):
                batch = connections[i : i + batch_size]
                batch_tasks = []

                for user_id, ws in batch:
                    try:
                        batch_tasks.append(self._safe_send(ws, message))
                    except Exception as e:
                        print(f"Error preparing send task for user {user_id}: {e}")
                        continue

                if batch_tasks:
                    # 배치 단위로 전송 처리
                    results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    send_tasks.extend(results)

                # 배치 사이에 짧은 대기 시간 추가
                await asyncio.sleep(0.01)

        except Exception as e:
            print(f"Error in broadcast_to_shard {shard_id}: {e}")

    def register_user(self, user_id: str, nickname: str, is_admin: bool = False):
        """사용자 정보 등록"""
        user_info = UserInfo(
            id=user_id, nickname=nickname, is_admin=is_admin, created_at=datetime.now()
        )
        self.user_info[user_id] = user_info
        # 캐시 무효화
        self.get_user_info.cache_clear()
        print(f"사용자 등록: {user_id}, 닉네임: {nickname}, 관리자: {is_admin}")

    def add_admin_message(self, message: ChatMessage):
        if message.room_id in self.admin_messages:
            self.admin_messages[message.room_id].append(message)
            # 최대 100개의 메시지만 유지
            if len(self.admin_messages[message.room_id]) > 100:
                self.admin_messages[message.room_id] = self.admin_messages[
                    message.room_id
                ][-100:]
            print(
                f"Admin message added to room {message.room_id}: {message.content}"
            )  # 디버깅용

    async def broadcast_admin_message(self, message: ChatMessage, room_id: str):
        """관리자 메시지를 브로드캐스트하고 요약 정보도 함께 전송"""
        try:
            # 메시지 저장
            self.add_admin_message(message)

            # 사용자 정보 가져오기
            user_info = self.get_user_info(message.user_id)
            if not user_info:
                print(f"Warning: User info not found for {message.user_id}")
                return

            # 브로드캐스트할 메시지 생성
            broadcast_message = {
                "id": str(uuid.uuid4()),
                "type": "admin",
                "user_id": message.user_id,
                "nickname": "관리자",  # 항상 "관리자"로 표시
                "content": message.content,
                "room_id": room_id,
                "timestamp": message.timestamp.isoformat(),
            }

            # 메시지 브로드캐스트
            await self.broadcast(broadcast_message, room_id)

        except Exception as e:
            print(f"Error broadcasting admin message: {e}")

    @lru_cache(maxsize=1000)
    def get_nickname(self, user_id: str) -> str:
        return f"사용자_{user_id[:8]}"

    async def broadcast_room_status(self):
        """모든 채팅방의 상태를 브로드캐스트"""
        try:
            # 각 방의 참가자 수 계산
            room_status = {}
            for room_id in CHAT_ROOMS.keys():
                active_count = len(self.room_participants[room_id])
                room_status[room_id] = active_count

            print(f"Broadcasting room status: {room_status}")

            # 상태 메시지 생성
            status_message = {
                "type": "room_status",
                "content": room_status,
                "timestamp": datetime.now().isoformat(),
            }

            # 모든 방에 상태 브로드캐스트
            for room_id in CHAT_ROOMS.keys():
                await self.broadcast(status_message, room_id)

        except Exception as e:
            print(f"Error broadcasting room status: {e}")

    async def connect(self, websocket: WebSocket, user_id: str, room_id: str):
        """연결 관리 - 개선된 버전"""
        try:
            # 1. 기본 유효성 검사
            if not websocket:
                print(f"Invalid WebSocket for user {user_id}")
                return False

            if room_id not in CHAT_ROOMS:
                print(f"Invalid room ID: {room_id}")
                return False

            # 2. 방 인원 수 제한 확인 (이미 연결된 사용자는 제외)
            current_participants = len(
                [p for p in self.room_participants[room_id] if p != user_id]
            )
            if current_participants >= MAX_CONNECTIONS_PER_ROOM:
                print(f"Room {room_id} is full")
                return False

            # 3. 이전 연결 정리
            await self._cleanup_previous_connection(user_id, room_id)

            try:
                # 4. 새 연결 저장 전에 기존 데이터 정리
                if room_id in self.active_connections:
                    if user_id in self.active_connections[room_id]:
                        del self.active_connections[room_id][user_id]
                    self.room_participants[room_id].discard(user_id)

                # 5. 새 연결 저장
                if room_id not in self.active_connections:
                    self.active_connections[room_id] = {}
                self.active_connections[room_id][user_id] = weakref.ref(websocket)
                self.room_participants[room_id].add(user_id)

                # 6. 샤드 할당
                shard_id = self._get_shard_id(user_id)
                if room_id not in self.connection_shards[shard_id]:
                    self.connection_shards[shard_id][room_id] = {}
                self.connection_shards[shard_id][room_id][user_id] = weakref.ref(
                    websocket
                )

                print(f"Successfully connected user {user_id} to room {room_id}")
                print(
                    f"Active connections in room {room_id}: {len(self.room_participants[room_id])}"
                )

                # 7. 연결 상태 브로드캐스트
                await self.broadcast_room_status()
                return True

            except Exception as e:
                print(f"Error during connection setup for user {user_id}: {e}")
                await self._cleanup_previous_connection(user_id, room_id)
                return False

        except Exception as e:
            print(f"Error in connect: {e}")
            await self._cleanup_previous_connection(user_id, room_id)
            return False

    async def _cleanup_previous_connection(self, user_id: str, room_id: str):
        """이전 연결 정리 - 개선된 버전"""
        try:
            if (
                room_id in self.active_connections
                and user_id in self.active_connections[room_id]
            ):
                old_ws_ref = self.active_connections[room_id][user_id]
                old_ws = old_ws_ref() if old_ws_ref else None

                if old_ws and not getattr(old_ws, "_closed", True):
                    try:
                        await old_ws.close(
                            code=1000, reason="New connection established"
                        )
                    except Exception as e:
                        print(f"Error closing old connection for user {user_id}: {e}")

                # 기존 연결 정보 제거
                self._remove_connection(user_id, room_id)

        except Exception as e:
            print(f"Error in cleanup_previous_connection: {e}")

    def _remove_connection(self, user_id: str, room_id: str):
        """연결 제거 - 개선된 버전"""
        try:
            # 기본 연결 정보 제거
            if room_id in self.active_connections:
                if user_id in self.active_connections[room_id]:
                    del self.active_connections[room_id][user_id]
                if not self.active_connections[room_id]:  # 방이 비었으면 방 정보도 제거
                    del self.active_connections[room_id]

            # 참가자 목록에서 제거
            if room_id in self.room_participants:
                self.room_participants[room_id].discard(user_id)

            # 샤드에서 제거
            shard_id = self._get_shard_id(user_id)
            if shard_id < len(self.connection_shards):
                if room_id in self.connection_shards[shard_id]:
                    if user_id in self.connection_shards[shard_id][room_id]:
                        del self.connection_shards[shard_id][room_id][user_id]
                    if not self.connection_shards[shard_id][
                        room_id
                    ]:  # 샤드의 방이 비었으면 방 정보도 제거
                        del self.connection_shards[shard_id][room_id]

        except Exception as e:
            print(f"Error in remove_connection: {e}")

    async def disconnect(self, user_id: str, room_id: str):
        """연결 종료 처리 - 개선된 버전"""
        try:
            # 연결 상태 확인
            ws_ref = self.active_connections.get(room_id, {}).get(user_id)
            ws = ws_ref() if ws_ref else None

            if ws and not getattr(ws, "_closed", True):
                try:
                    await ws.close(code=1000, reason="Disconnected by server")
                except Exception as e:
                    print(f"Error closing WebSocket for user {user_id}: {e}")

            # 연결 정보 정리
            self._remove_connection(user_id, room_id)
            print(f"User {user_id} disconnected from room {room_id}")

            # 방 상태 업데이트
            await self.broadcast_room_status()

        except Exception as e:
            print(f"Error in disconnect: {e}")
            # 에러가 발생하더라도 연결 정보는 정리
            self._remove_connection(user_id, room_id)

    async def _periodic_cleanup(self):
        """주기적으로 연결과 리소스를 정리하는 메서드"""
        while True:
            try:
                print("Starting periodic cleanup...")

                # 각 채팅방의 연결 상태 확인
                for room_id in list(self.active_connections.keys()):
                    for user_id, ws_ref in list(
                        self.active_connections[room_id].items()
                    ):
                        ws = ws_ref() if ws_ref else None
                        if not ws or getattr(ws, "_closed", True):
                            await self._cleanup_previous_connection(user_id, room_id)
                            print(
                                f"Cleaned up disconnected user {user_id} from room {room_id}"
                            )

                # 메시지 큐 정리
                for shard_id in range(SHARD_COUNT):
                    for room_id in list(self.shard_queues[shard_id].keys()):
                        queue = self.shard_queues[shard_id][room_id]
                        while queue.qsize() > MESSAGE_QUEUE_SIZE:
                            try:
                                await queue.get()
                            except Exception as e:
                                print(f"Error cleaning message queue: {e}")
                                break

                # 메모리 정리
                gc.collect()

                print("Periodic cleanup completed")
                await asyncio.sleep(CLEANUP_INTERVAL)

            except Exception as e:
                print(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(60)  # 에러 발생 시 1분 후 재시도

    async def _periodic_error_reset(self):
        """주기적으로 에러 카운트를 초기화하는 메서드"""
        while True:
            try:
                self.error_counts.clear()
                await asyncio.sleep(ERROR_COUNT_RESET_INTERVAL)
            except Exception as e:
                print(f"Error in error count reset: {e}")
                await asyncio.sleep(60)


manager = ConnectionManager()


# 라우트 핸들러
@app.get("/streaming", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    room_status = {
        room_id: len(manager.room_participants.get(room_id, set()))
        for room_id in CHAT_ROOMS.keys()
    }
    return templates.TemplateResponse(
        "streaming.html",
        {"request": request, "chat_rooms": CHAT_ROOMS, "room_status": room_status},
    )


# 비밀번호 해싱 함수
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# 사용자 인증 함수
def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"User not found: {username}")  # 디버깅 로그
        raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호")

    hashed_password = hash_password(password)
    print(
        f"Login attempt - Username: {username}, Hashed password: {hashed_password}"
    )  # 디버깅 로그
    print(f"Stored password: {user.password}")  # 디버깅 로그

    if user.password != hashed_password:
        print(f"Password mismatch for user: {username}")  # 디버깅 로그
        raise HTTPException(status_code=401, detail="잘못된 사용자명 또는 비밀번호")

    return user


@app.post("/user/register")
async def register_user(
    nickname: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        print(f"회원가입 시도 - 닉네임: {nickname}, 사용자명: {username}")  # 디버깅용

        # 사용자명 중복 확인
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"사용자명 중복: {username}")  # 디버깅용
            raise HTTPException(status_code=400, detail="이미 사용 중인 사용자명입니다")

        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)

        print(f"새 사용자 생성 - ID: {user_id}")  # 디버깅용

        # 데이터베이스에 사용자 저장
        db_user = User(
            id=user_id,
            nickname=nickname,
            username=username,
            password=hashed_password,
            is_admin=False,  # 일반 사용자는 관리자가 아님
        )
        db.add(db_user)
        db.commit()

        print(f"사용자 저장 완료 - ID: {user_id}")  # 디버깅용

        # 저장된 사용자 확인
        saved_user = db.query(User).filter(User.id == user_id).first()
        if not saved_user:
            print(
                f"오류: 사용자가 데이터베이스에 저장되지 않음 - ID: {user_id}"
            )  # 디버깅용
            raise HTTPException(
                status_code=500, detail="사용자 저장 중 오류가 발생했습니다"
            )

        manager.register_user(user_id, nickname, is_admin=False)

        return {"user_id": user_id, "nickname": nickname, "is_admin": False}
    except HTTPException as e:
        print(f"회원가입 실패: {str(e)}")  # 디버깅용
        raise e
    except Exception as e:
        print(f"회원가입 중 예외 발생: {str(e)}")  # 디버깅용
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다")


@app.post("/user/login")
async def login_user(
    username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    try:
        print(f"Login attempt for username: {username}")  # 디버깅 로그

        # 사용자 인증
        user = authenticate_user(db, username, password)

        # 관리자 여부 확인 (데이터베이스에서 직접 확인)
        is_admin = db.query(User).filter(User.id == user.id).first().is_admin

        print(
            f"User authenticated - ID: {user.id}, Nickname: {user.nickname}, Is Admin: {is_admin}"
        )  # 디버깅 로그

        # ConnectionManager에 사용자 정보 등록
        manager.register_user(user.id, user.nickname, is_admin=is_admin)

        return {"user_id": user.id, "nickname": user.nickname, "is_admin": is_admin}
    except HTTPException as e:
        print(f"Login failed: {str(e)}")  # 디버깅 로그
        raise e


@app.websocket("/ws/chat/{user_id}/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: str, room_id: str, db: Session = Depends(get_db)
):
    if not manager.initialized:
        await manager.initialize()

    connection_established = False
    error_count = 0  # 에러 카운트 추가
    MAX_ERRORS = 3  # 최대 허용 에러 횟수

    try:
        # 1. 방 유효성 검사
        if room_id not in CHAT_ROOMS:
            print(f"Invalid room ID: {room_id}")
            await websocket.close(code=4000, reason="Invalid room")
            return

        print(
            f"New WebSocket connection request from user {user_id} for room {room_id}"
        )

        # 2. WebSocket 연결 수락
        await websocket.accept()
        connection_established = True
        print(f"WebSocket connection accepted for user {user_id}")

        # 3. 연결 상태 확인 메시지 전송
        await websocket.send_json({"type": "connection_established"})

        # 4. 사용자 정보 조회 및 등록
        user = db.query(User).filter(User.id == user_id).first()
        nickname = user.nickname if user else f"사용자_{user_id[:8]}"
        manager.register_user(user_id, nickname, is_admin=False)

        # 5. ConnectionManager에 연결 추가
        if not await manager.connect(websocket, user_id, room_id):
            await websocket.close(code=4000, reason="Connection failed")
            return

        # 6. 입장 메시지 브로드캐스트
        await manager.broadcast(
            {
                "id": str(uuid.uuid4()),
                "type": "system",
                "content": f"{nickname}님이 입장하셨습니다.",
                "nickname": "시스템",
                "timestamp": datetime.now().isoformat(),
                "room_id": room_id,
            },
            room_id,
        )

        # 7. 메시지 수신 루프
        while True:
            try:
                # 연결 상태 확인
                if getattr(websocket, "_closed", True):
                    print(f"WebSocket closed for user {user_id}")
                    break

                data = await websocket.receive_text()
                if not data:
                    continue

                try:
                    message_data = json.loads(data)

                    # ping/pong 처리
                    if message_data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                        error_count = 0  # 성공적인 통신 시 에러 카운트 초기화
                        continue

                    content = message_data.get("content", "")
                    if not content:
                        continue

                    # 메시지 브로드캐스트
                    await manager.broadcast(
                        {
                            "id": str(uuid.uuid4()),
                            "type": "user",
                            "user_id": user_id,
                            "nickname": nickname,
                            "content": content,
                            "room_id": room_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                        room_id,
                    )
                    error_count = 0  # 성공적인 메시지 전송 시 에러 카운트 초기화

                except json.JSONDecodeError as e:
                    print(f"Invalid JSON from user {user_id}: {e}")
                    error_count += 1

            except WebSocketDisconnect:
                print(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                error_count += 1
                print(f"Error processing message from user {user_id}: {e}")

                # 에러 횟수가 임계값을 초과하면 연결 종료
                if error_count >= MAX_ERRORS:
                    print(f"Too many errors for user {user_id}, closing connection")
                    await websocket.close(code=1011, reason="Too many errors")
                    break

                # 잠시 대기 후 계속
                await asyncio.sleep(1)
                continue

    except WebSocketDisconnect:
        print(f"WebSocket disconnected during setup for user {user_id}")
    except Exception as e:
        print(f"Error in websocket setup for user {user_id}: {e}")
    finally:
        if connection_established:
            try:
                await manager.disconnect(user_id, room_id)
                await manager.broadcast(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "system",
                        "content": f"{nickname}님이 퇴장하셨습니다.",
                        "nickname": "시스템",
                        "room_id": room_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    room_id,
                )
            except Exception as e:
                print(f"Error in disconnect handling for user {user_id}: {e}")


async def handle_disconnect(user_id: str, room_id: str, db: Session, redis):
    """연결 종료 처리를 위한 함수"""
    try:
        # Redis에서 사용자 정보 조회
        if redis_pool:
            try:
                user_info = await redis_pool.hgetall(f"user:{user_id}")
                nickname = user_info.get("nickname", "알 수 없는 사용자")
            except Exception as e:
                print(f"Redis 조회 실패: {e}")
                # DB에서 사용자 정보 조회
                user = db.query(User).filter(User.id == user_id).first()
                nickname = user.nickname if user else "알 수 없는 사용자"
        else:
            # Redis가 없는 경우 DB에서 조회
            user = db.query(User).filter(User.id == user_id).first()
            nickname = user.nickname if user else "알 수 없는 사용자"

        # 퇴장 메시지 저장
        current_time = datetime.now()
        db_message = Message(
            user_id=user_id,
            content=f"{nickname}님이 퇴장하셨습니다.",
            room_id=room_id,
            type="system",
            timestamp=current_time,
        )
        db.add(db_message)
        db.commit()

        # Redis에 상태 업데이트
        if redis_pool:
            try:
                await redis_pool.hset(
                    f"user:{user_id}",
                    mapping={
                        "status": "disconnected",
                        "room_id": room_id,
                        "last_seen": current_time.isoformat(),
                    },
                )
            except Exception as e:
                print(f"Redis 상태 업데이트 실패: {e}")

        # 브로드캐스트
        await manager.broadcast(
            {
                "type": "system",
                "content": f"{nickname}님이 퇴장하셨습니다.",
                "timestamp": current_time.isoformat(),
            },
            room_id,
        )
        await manager.broadcast_room_status()

    except Exception as e:
        print(f"Error handling disconnect: {e}")
        db.rollback()


# Redis 풀 초기화
async def init_redis_pool():
    global redis_pool
    try:
        redis_pool = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=REDIS_POOL_SIZE,
            retry_on_timeout=True,
            socket_connect_timeout=5.0,
            socket_timeout=5.0,
        )
        # Redis 연결 테스트
        await redis_pool.ping()
        print("Redis 연결 성공")
    except Exception as e:
        print(f"Redis 연결 실패: {e}")
        print("Redis 없이 계속 진행합니다.")
        redis_pool = None


# 데이터베이스 최적화 설정
def setup_database():
    engine = create_engine(
        f"sqlite:///{DB_FILE}",
        poolclass=QueuePool,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_recycle=1800,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=100000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=30000000000")
        cursor.close()

    return engine


# 주기적인 가비지 컬렉션
def periodic_cleanup():
    while True:
        gc.collect()
        time.sleep(300)  # 5분마다 실행


# 앱 시작 시 초기화
@app.on_event("startup")
async def startup_event():
    if not os.path.exists(DB_FILE):
        print("데이터베이스 파일이 없습니다. 초기화를 시작합니다...")
        init_db()
    else:
        print("기존 데이터베이스를 사용합니다.")

    # Redis 풀 초기화
    await init_redis_pool()

    # 데이터베이스 최적화 설정 적용
    setup_database()

    # ConnectionManager 초기화
    await manager.initialize()

    # 가비지 컬렉션 스레드 시작
    gc_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    gc_thread.start()


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 리소스 정리"""
    print("Starting application shutdown...")  # 디버깅 로그

    try:
        # ConnectionManager 종료
        await manager.shutdown()

        # Redis 연결 종료
        if redis_pool:
            try:
                await redis_pool.close()
                print("Redis connection closed")  # 디버깅 로그
            except Exception as e:
                print(f"Error closing Redis connection: {e}")

        print("Application shutdown completed")  # 디버깩 로그

    except Exception as e:
        print(f"Error during application shutdown: {e}")


@app.get("/messages/{room_id}")
async def get_messages(
    room_id: str,
    before: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """이전 메시지 조회 API"""
    try:
        # 기본 쿼리 설정
        query = db.query(Message).filter(Message.room_id == room_id)

        # 타임스탬프 기준으로 필터링
        if before:
            try:
                before_time = datetime.fromisoformat(before)
                query = query.filter(Message.timestamp < before_time)
            except ValueError:
                print(f"잘못된 타임스탬프 형식: {before}")

        # 최신 메시지부터 가져오기 (limit + 1개를 가져와서 더 있는지 확인)
        messages = query.order_by(Message.timestamp.desc()).limit(limit + 1).all()

        # 실제로 반환할 메시지 (limit 개수만큼)
        return_messages = messages[:limit]

        # 메시지 형식 변환
        formatted_messages = []
        for message in return_messages:
            formatted_message = {
                "id": str(uuid.uuid4()),  # 각 메시지에 고유 ID 부여
                "type": message.type,
                "content": message.content,
                "user_id": message.user_id,
                "nickname": manager.get_nickname(message.user_id),
                "timestamp": message.timestamp.isoformat(),
                "room_id": message.room_id,
            }
            formatted_messages.append(formatted_message)

        return formatted_messages

    except Exception as e:
        print(f"메시지 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail="메시지 조회 중 오류가 발생했습니다"
        )


if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config(
        app=app, host="0.0.0.0", port=8000, loop="asyncio", workers=1
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
