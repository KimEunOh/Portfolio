import requests

# 서버의 IP 또는 도메인 주소와 포트를 입력
SERVER_URL = "http://192.168.10.184:8000/query"  # 예: "http://192.168.0.10:8000/query"


def query_server(prompt: str):
    """
    다른 컴퓨터(클라이언트)에서 FastAPI 서버로 프롬프트를 전송하고 결과를 반환합니다.
    :param prompt: 모델에게 보낼 프롬프트 문자열
    :return: 서버가 반환하는 응답(딕셔너리 형태)
    """
    data = {"prompt": prompt}

    try:
        response = requests.post(SERVER_URL, json=data, timeout=60)
        response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킵니다
        return response.json()  # JSON 형식의 응답을 딕셔너리로 변환하여 반환합니다
    except requests.exceptions.HTTPError as http_err:
        print("HTTP 오류:", http_err)
        print("서버 응답 내용:", response.text)
    except requests.exceptions.RequestException as req_err:
        print("요청 관련 오류:", req_err)


if __name__ == "__main__":
    user_prompt = "안녕하세요! 문학동네 개발 IP를 알려주세요."
    response_data = query_server(user_prompt)
    print("서버 응답:", response_data)


# # A 컴퓨터의 IP 주소와 Ollama 서버 포트
# ollama_server_url = "http://219.250.196.30:11435"

# # 사용할 모델 이름
# model_name = "hf.co/teddylee777/EEVE-Korean-Instruct-10.8B-v1.0-gguf:Q4_0"

# # 질문 내용
# prompt = "서울은 어느 수도야?"

# # Ollama API 엔드포인트
# url = f"{ollama_server_url}/api/generate"

# # 요청 페이로드
# payload = {"model": model_name, "prompt": prompt}

# # HTTP POST 요청 보내기
# response = requests.post(url, json=payload)

# # 응답에서 답변 추출
# if response.status_code == 200:
#     answer = response.json().get("output")
#     print("답변:", answer)
# else:
#     print("오류 발생:", response.status_code, response.text)


# curl -X POST http://http://219.250.196.30:11435/api/generate -d '{"model": "hf.co/teddylee777/EEVE-Korean-Instruct-10.8B-v1.0-gguf:Q4_0", "prompt": "안녕하세요, 오늘 날씨는 어떤가요?"}'
