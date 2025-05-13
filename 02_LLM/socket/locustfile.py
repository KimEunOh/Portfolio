import time
import json
import uuid
from locust import HttpUser, task, between, events
from locust.exception import StopUser
import websocket
from datetime import datetime
import random


class WebSocketClient:
    def __init__(self, host):
        self.host = host.replace("http://", "").replace("https://", "")
        self.ws = None
        self.connected = False
        self.connect_timeout = 5  # 연결 타임아웃 5초
        self.retry_count = 3  # 최대 재시도 횟수

    def connect(self, user_id: str, room_id: str):
        """WebSocket 연결 설정"""
        for attempt in range(self.retry_count):
            try:
                ws_url = f"ws://{self.host}/ws/chat/{user_id}/{room_id}"
                print(f"Connecting to WebSocket URL: {ws_url} (attempt {attempt + 1})")

                # 기존 연결 정리
                self.disconnect()

                # 새로운 연결 생성
                self.ws = websocket.create_connection(
                    ws_url,
                    header=["Host: " + self.host],
                    enable_multithread=True,
                    timeout=self.connect_timeout,
                )

                # 연결 확인
                self.ws.send(json.dumps({"type": "ping"}))
                response = json.loads(self.ws.recv())
                if (
                    response.get("type") == "pong"
                    or response.get("type") == "connection_established"
                ):
                    self.connected = True
                    print(
                        f"Successfully connected to WebSocket (attempt {attempt + 1})"
                    )
                    return self.ws

            except Exception as e:
                print(f"WebSocket connection attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(1)  # 재시도 전 1초 대기
                continue

        self.connected = False
        raise Exception(f"Failed to connect after {self.retry_count} attempts")

    def send_message(self, message: dict):
        """메시지 전송"""
        if not self.ws or not self.connected:
            raise Exception("WebSocket is not connected")

        try:
            self.ws.send(json.dumps(message))
        except Exception as e:
            print(f"Send message failed: {e}")
            self.connected = False
            raise

    def receive_message(self):
        """메시지 수신"""
        if not self.ws or not self.connected:
            raise Exception("WebSocket is not connected")

        try:
            return self.ws.recv()
        except Exception as e:
            print(f"Receive message failed: {e}")
            self.connected = False
            raise

    def disconnect(self):
        """연결 종료"""
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            finally:
                self.ws = None
                self.connected = False


class ChatUser(HttpUser):
    wait_time = between(1, 3)  # 작업 사이의 대기 시간 단축
    host = "http://localhost:8000"  # 기본 호스트 설정

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_client = None
        self.user_id = str(uuid.uuid4())
        self.room_id = None
        self.nickname = f"User_{self.user_id[:8]}"
        self.available_rooms = ["room1", "room2", "room3", "room4"]
        self.connection_retry_count = 0
        self.max_connection_retries = 3

    def on_start(self):
        """사용자 세션 시작시 실행"""
        try:
            # 초기 방 선택
            self.select_new_room()

            # WebSocket 연결
            self.ws_client = WebSocketClient(self.host)
            try:
                self.ws_client.connect(self.user_id, self.room_id)
                self.connection_retry_count = 0  # 연결 성공 시 카운터 리셋
            except Exception as e:
                print(f"Initial WebSocket connection failed: {e}")
                raise StopUser()

        except Exception as e:
            print(f"Error in on_start: {e}")
            raise StopUser()

    def select_new_room(self):
        """새로운 채팅방 선택"""
        self.room_id = random.choice(self.available_rooms)

    def on_stop(self):
        """사용자 세션 종료시 실행"""
        if self.ws_client:
            self.ws_client.disconnect()

    @task(20)
    def send_chat_message(self):
        """채팅 메시지 전송"""
        if not self.ws_client or not self.ws_client.connected:
            if self.connection_retry_count < self.max_connection_retries:
                try:
                    print(
                        f"Attempting to reconnect (attempt {self.connection_retry_count + 1})"
                    )
                    self.ws_client = WebSocketClient(self.host)
                    self.ws_client.connect(self.user_id, self.room_id)
                    self.connection_retry_count += 1
                except Exception as e:
                    print(f"Reconnection failed: {e}")
                    return
            else:
                print("Max reconnection attempts reached")
                return

        message = {
            "type": "user",
            "content": f"Test message from {self.nickname} at {datetime.now().isoformat()}",
            "room_id": self.room_id,
            "user_id": self.user_id,
        }

        start_time = time.time()
        try:
            # 메시지 전송
            self.ws_client.send_message(message)

            # 응답 수신
            response = self.ws_client.receive_message()

            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="WebSocket Message",
                name="Chat Message",
                response_time=total_time,
                response_length=len(response),
                exception=None,
            )

            # 성공적인 메시지 전송 후 재시도 카운터 리셋
            self.connection_retry_count = 0

        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="WebSocket Message",
                name="Chat Message",
                response_time=total_time,
                response_length=0,
                exception=e,
            )

    @task(1)
    def change_room(self):
        """가끔 다른 방으로 이동"""
        try:
            # 이전 연결 종료
            if self.ws_client:
                self.ws_client.disconnect()

            # 새로운 방 선택
            old_room = self.room_id
            while self.room_id == old_room:
                self.select_new_room()

            # 새로운 방에 연결
            self.ws_client = WebSocketClient(self.host)
            self.ws_client.connect(self.user_id, self.room_id)
            self.connection_retry_count = 0  # 새로운 방 연결 성공 시 카운터 리셋

        except Exception as e:
            print(f"Error changing room: {e}")
            if self.connection_retry_count < self.max_connection_retries:
                self.connection_retry_count += 1
