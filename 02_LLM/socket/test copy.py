from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>실시간 채팅</title>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        #chat-box {
            width: 90%;
            max-width: 600px;
            height: 400px;
            border: 1px solid #ccc;
            padding: 10px;
            overflow-y: scroll;
            margin-bottom: 10px;
            display: flex;
            flex-direction: column;
        }
        #message-form {
            display: flex;
            width: 90%;
            max-width: 600px;
        }
        #message-input {
            flex: 1;
            padding: 10px;
            font-size: 14px;
        }
        #send-button {
            padding: 10px 20px;
            font-size: 14px;
        }
        .message {
            margin: 5px 0;
            padding: 5px 10px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .my-message {
            background-color: #dcf8c6;
            align-self: flex-end;
            text-align: right;
        }
        .other-message {
            background-color: #f1f0f0;
            align-self: flex-start;
            text-align: left;
        }
    </style>
</head>
<body>
    <h1>실시간 채팅</h1>
    <div>
        <label for="room-id">방 번호:</label>
        <input type="text" id="room-id" placeholder="방 번호를 입력하세요" required />
        <button id="join-room">입장</button>
    </div>
    <div id="chat-box" style="display: none;"></div>
    <form id="message-form" style="display: none;">
        <input type="text" id="message-input" placeholder="메시지를 입력하세요..." autocomplete="off" required />
        <button type="submit" id="send-button">전송</button>
    </form>

    <script>
        let ws;
        let clientId = Date.now(); // 클라이언트 ID를 현재 시간으로 설정하여 고유하게 만듦

        document.getElementById('join-room').addEventListener('click', function() {
            const roomId = document.getElementById('room-id').value.trim();
            if (roomId) {
                connectToRoom(roomId);
                document.getElementById('chat-box').style.display = 'flex';
                document.getElementById('message-form').style.display = 'flex';
            }
        });

        function connectToRoom(roomId) {
            ws = new WebSocket(`ws://localhost:8000/ws/${roomId}/${clientId}`);

            ws.onmessage = function(event) {
                const chatBox = document.getElementById('chat-box');
                const message = document.createElement('div');
                message.classList.add('message');

                if (event.data.startsWith(`Client #${clientId} says:`)) {
                    message.classList.add('my-message');
                    message.textContent = `나: ${event.data.replace(`Client #${clientId} says:`, '').trim()}`;
                } else {
                    message.classList.add('other-message');
                    message.textContent = event.data;
                }

                chatBox.appendChild(message);
                chatBox.scrollTop = chatBox.scrollHeight; // 새로운 메시지가 추가되면 스크롤을 아래로 이동
            };

            document.getElementById('message-form').addEventListener('submit', function(event) {
                event.preventDefault();
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                if (message) {
                    ws.send(message);
                    input.value = '';
                }
            });
        }
    </script>
</body>
</html>

"""


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
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, client_id: int):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client #{client_id} says: {data}", room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast(f"Client #{client_id} left the chat", room_id)
