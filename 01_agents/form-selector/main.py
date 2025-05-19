# requirements.txt에 다음 패키지 포함 필요:
# fastapi, uvicorn, langchain, langchain_openai, pydantic

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from form_selector.schema import UserInput
from form_selector.service import classify_and_get_template
import os
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse

# .env 파일 로드 (OPENAI_API_KEY 등을 환경변수로 로드)
load_dotenv()

# FastAPI 앱 생성
app = FastAPI()

# 정적 파일 마운트 (static 폴더를 /ui 경로로 접근 가능하게 함)
# HTML, CSS, JS 파일들을 static 폴더에 위치시킵니다.
app.mount(
    "/ui",
    StaticFiles(
        directory=os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
    ),
    name="static",
)


@app.get("/")
async def read_root():
    return {"message": "Form Selector API. UI는 /ui 로 접속하세요."}


@app.post("/form-selector")
async def form_selector_endpoint(user_input: UserInput):
    try:
        result = classify_and_get_template(user_input)

        if "error" in result:
            error_type = result.get("error")
            if error_type == "PARSING_FAILED_ASK_USER":
                # LLM 파싱 최종 실패로 사용자에게 되묻는 경우는 200 OK로 응답.
                # 프론트엔드에서 이 응답을 보고 사용자에게 선택지를 제시하는 등의 UI 처리.
                return result
            elif error_type == "TEMPLATE_NOT_FOUND":
                # RAG 검색 실패 또는 지원하지 않는 양식의 경우 404 에러.
                # detail에 result 전체를 전달하여 프론트에서 활용 가능하게 함.
                raise HTTPException(status_code=404, detail=result)
            else:
                # 기타 정의된 에러 타입 (예: "UNEXPECTED_PROCESSING_ERROR")
                raise HTTPException(status_code=500, detail=result)

        # 성공적인 결과 반환
        return result
    except HTTPException as http_exc:
        # 이미 HTTPException으로 처리된 경우 그대로 다시 발생
        raise http_exc
    except Exception as e:
        # 그 외 예측하지 못한 일반적인 서버 오류
        print(f"Unexpected server error: {e}")  # 서버 로그에 상세 오류 기록
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message_to_user": "서버 내부 오류가 발생했습니다.",
            },
        )


# 루트 경로 ("/") 접근 시 UI 페이지로 리디렉션 또는 기본 페이지 안내 (선택적)
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>Form Selector API</title>
        </head>
        <body>
            <h1>Form Selector API</h1>
            <p>Test UI is available at <a href="/ui/index.html">/ui/index.html</a>.</p>
        </body>
    </html>
    """


# FastAPI 엔트리포인트 및 라우터 정의 예정
