from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from openai import OpenAI

app = Flask(__name__)

# .env 파일에서 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
OpenAI.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()


def get_gpt4_response(prompt):
    try:
        # GPT-4 API 호출
        response = client.response.create(
            model="gpt-4o",
            messages=prompt,
            temperature=0.7,
        )

        # 응답에서 텍스트 추출
        return response.output_text

    except Exception as e:
        return f"에러가 발생했습니다: {str(e)}"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    user_message = data.get("message", "")
    response = get_gpt4_response(user_message)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)
