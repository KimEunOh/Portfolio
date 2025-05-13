from flask import Flask, request, render_template_string, session, jsonify
import requests
import json

app = Flask(__name__)
# app.secret_key = "YOUR_SECRET_KEY"  # 실제 배포 시 안전한 키로 교체

# FastAPI 서버 주소
SERVER_URL = "http://192.168.10.184:8000/query"

# 초기 안내 메시지
WELCOME_MESSAGE = "안녕하세요! 무엇을 도와드릴까요?"


def query_server(prompt: str):
    """
    FastAPI 서버로 메시지를 전송하고, 서버의 응답을 받아오는 함수.
    FastAPI는 {"response": "..."} 형태로 반환.
    """
    data = {"prompt": prompt}
    try:
        response = requests.post(SERVER_URL, json=data, timeout=120)
        response.raise_for_status()
        # 예: {"response": "..."}
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {"response": f"HTTP 오류: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        return {"response": f"요청 오류: {req_err}"}


# 메인 페이지: Bootstrap + JavaScript(AJAX) 기반 채팅 UI
html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>엔투 챗봇 테스트</title>
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css">
    <style>
        body {
            background-color: #f8f9fa;
        }
        .chat-container {
            max-width: 700px;
            margin: 30px auto;
            background-color: #fff;
            border-radius: 8px;
            padding: 20px;
        }
        .chat-bubble {
            position: relative;
            margin: 10px 0;
            padding: 12px 15px;
            border-radius: 15px;
            clear: both;
            display: inline-block;
            max-width: 80%;
            font-size: 15px;
            line-height: 1.4em;
        }
        .user-message {
            background-color: #e1ffc7;
            float: right;
        }
        .assistant-message {
            background-color: #f8f9fa;
            float: left;
        }
        .message-input-area {
            margin-top: 20px;
        }
        .spinner {
            font-size: 0.9em;
            color: #888;
        }
    </style>
</head>
<body>

<div class="container chat-container shadow">
    <h3 class="mb-4">엔투 모델 테스트</h3>
    
    <!-- 채팅 내역이 들어갈 영역 -->
    <div id="chat-history">
        <!-- 기존 대화내역이 JavaScript로 로드되어 표시됩니다. -->
    </div>

    <div class="message-input-area">
        <div class="input-group">
            <input type="text" id="user_input" class="form-control" placeholder="메시지를 입력하세요" aria-label="User input">
            <div class="input-group-append">
                <button class="btn btn-primary" type="button" onclick="sendMessage()">전송</button>
            </div>
        </div>
    </div>

    <div class="mt-3">
        <button class="btn btn-outline-secondary float-right" onclick="clearChat()">대화 초기화</button>
    </div>
    <div class="clearfix"></div>
</div>

<!-- Bootstrap JS, jQuery 등 -->
<script src="https://cdn.jsdelivr.net/npm/jquery@3.5.1/dist/jquery.slim.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>

<script>
    // 페이지 로드 시 대화내역 불러오기
    window.onload = function() {
        fetchConversation();
    };

    // Flask 서버에서 대화내역을 가져와서 표시
    function fetchConversation() {
        fetch("/get_conversation")
            .then(response => response.json())
            .then(data => {
                // data는 [{role: "...", text: "..."}] 형태
                renderConversation(data);
            })
            .catch(err => console.error("Error fetching conversation:", err));
    }

    // 채팅 기록을 HTML로 렌더링
    function renderConversation(conversation) {
        const chatHistory = document.getElementById("chat-history");
        chatHistory.innerHTML = "";  // 기존 내용 초기화

        if (conversation.length === 0) {
            // 아무 메시지도 없을 경우 웰컴 메시지 표시
            const welcomeBubble = document.createElement("div");
            welcomeBubble.innerText = "{{ welcome_message }}";
            chatHistory.appendChild(welcomeBubble);
        } else {
            // 대화가 있을 경우, 순서대로 말풍선 추가
            conversation.forEach(msg => {
                const bubble = document.createElement("div");
                bubble.classList.add("chat-bubble");
                bubble.innerText = msg.text;
                if (msg.role === "user") {
                    bubble.classList.add("user-message");
                } else {
                    bubble.classList.add("assistant-message");
                }
                chatHistory.appendChild(bubble);
                const clearDiv = document.createElement("div");
                clearDiv.classList.add("clearfix");
                chatHistory.appendChild(clearDiv);
            });
        }

        // 맨 아래로 스크롤
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // 메시지 전송
    function sendMessage() {
        const userInput = document.getElementById("user_input");
        const userText = userInput.value.trim();
        if (!userText) return;

        // 사용자 메시지를 채팅창에 바로 추가
        appendUserMessage(userText);

        // 로딩 표시용 가짜 말풍선 추가
        const loadingBubble = appendAssistantMessage("응답을 가져오는 중...");

        // 서버로 AJAX POST
        fetch("/send_message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_input: userText })
        })
        .then(response => response.json())
        .then(data => {
            // data는 { "response": "실제 답변" } 형태
            loadingBubble.innerText = data.response;
        })
        .catch(err => {
            // 오류 발생 시
            loadingBubble.innerText = "서버 에러가 발생했습니다.";
        })
        .finally(() => {
            // 입력 필드 비우기
            userInput.value = "";
            // 맨 아래로 스크롤
            const chatHistory = document.getElementById("chat-history");
            chatHistory.scrollTop = chatHistory.scrollHeight;
        });
    }

    // 사용자 말풍선 UI에 추가
    function appendUserMessage(text) {
        const chatHistory = document.getElementById("chat-history");
        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble", "user-message");
        bubble.innerText = text;
        chatHistory.appendChild(bubble);

        const clearDiv = document.createElement("div");
        clearDiv.classList.add("clearfix");
        chatHistory.appendChild(clearDiv);
    }

    // 어시스턴트 말풍선 UI 추가
    function appendAssistantMessage(text) {
        const chatHistory = document.getElementById("chat-history");
        const bubble = document.createElement("div");
        bubble.classList.add("chat-bubble", "assistant-message");
        bubble.innerText = text;
        chatHistory.appendChild(bubble);

        const clearDiv = document.createElement("div");
        clearDiv.classList.add("clearfix");
        chatHistory.appendChild(clearDiv);

        return bubble; // 갱신에 활용하기 위해 반환
    }

    // 대화 초기화
    function clearChat() {
        fetch("/clear_chat")
            .then(response => {
                // 대화 기록 초기화 후 다시 불러오기
                fetchConversation();
            })
            .catch(err => console.error("Error clearing conversation:", err));
    }
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(html_template, welcome_message=WELCOME_MESSAGE)


@app.route("/get_conversation", methods=["GET"])
def get_conversation():
    """세션에 저장된 대화 내역을 반환"""
    if "conversation" not in session:
        session["conversation"] = []
    return jsonify(session["conversation"])


@app.route("/send_message", methods=["POST"])
def send_message():
    """
    사용자 메시지를 받아 세션에 저장하고,
    FastAPI 서버에 전송 후 받은 메시지도 세션에 저장한 뒤 반환
    """
    if "conversation" not in session:
        session["conversation"] = []

    data = request.json
    user_text = data.get("user_input", "").strip()
    if not user_text:
        return jsonify({"response": "메시지가 비어있습니다."})

    # 사용자 메시지 기록
    session["conversation"].append({"role": "user", "text": user_text})

    # FastAPI 서버로 전송
    response_data = query_server(user_text)
    # FastAPI가 {"response": "..."} 형태로 준다고 가정
    server_reply = response_data.get("response", "서버 응답을 가져올 수 없습니다.")

    # 어시스턴트 메시지 기록
    session["conversation"].append({"role": "assistant", "text": server_reply})
    session.modified = True  # 세션 수정 사항 반영

    return jsonify({"response": server_reply})


@app.route("/clear_chat", methods=["GET"])
def clear_chat():
    """대화 내역 초기화"""
    session.pop("conversation", None)
    return jsonify({"result": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)
