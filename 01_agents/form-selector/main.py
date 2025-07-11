# requirements.txt에 다음 패키지 포함 필요:
# fastapi, uvicorn, langchain, langchain_openai, pydantic

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from form_selector.schema import UserInput
from form_selector.service import classify_and_extract_slots_for_template
import os
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
import httpx
import json

# schema와 service에서 추가된 모델/함수 임포트
from form_selector import schema as form_schema  # schema 전체를 form_schema로 임포트
from form_selector.service import (
    get_approval_info,
    convert_form_data_to_api_payload,
)  # 새로 추가한 서비스 함수

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
    return RedirectResponse(url="/ui/login.html")


@app.post("/form-selector")
async def form_selector_endpoint(user_input: UserInput):
    try:
        result = classify_and_extract_slots_for_template(user_input)

        if "error" in result:
            error_type = result.get("error")
            if (
                error_type == "CLASSIFICATION_FAILED"
                or error_type == "TEMPLATE_NOT_FOUND"
                or error_type == "CLASSIFICATION_UNEXPECTED_ERROR"
            ):
                if error_type == "TEMPLATE_NOT_FOUND":
                    raise HTTPException(status_code=404, detail=result)
                return result
            elif error_type == "UNEXPECTED_PROCESSING_ERROR":
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


# --- 결재자 정보 조회 엔드포인트 --- #
@app.post("/approver-info", response_model=form_schema.ApproverInfoResponse)
async def approver_info_endpoint(request: form_schema.ApproverInfoRequest):
    try:
        result = get_approval_info(request)
        if result.code != 1:  # 실패 코드로 가정 (예: 0 또는 음수)
            # 서비스 함수 내부에서 HTTPException을 발생시키지 않는 경우, 여기서 처리
            # 여기서는 code=1이 성공이라고 가정하고, 그 외는 일반 오류로 처리하거나
            # service 함수가 구체적인 HTTPException을 발생시키도록 수정할 수 있음.
            # 지금은 간단히 500 오류로 처리.
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "APPROVER_INFO_FAILED",
                    "message_to_user": result.message,
                    "details": result.data,  # 또는 result 전체
                },
            )
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Unexpected server error in /approver-info: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message_to_user": "결재 정보를 가져오는 중 서버 내부 오류가 발생했습니다.",
            },
        )


# --- END 결재자 정보 조회 엔드포인트 --- #


# --- 외부 myLine API 직접 호출 엔드포인트 --- #
@app.post("/myLine", response_model=form_schema.ApproverInfoResponse)
async def fetch_my_line_endpoint(request: form_schema.ApproverInfoRequest):
    logging.info(
        f"외부 myLine API 직접 호출 요청: mstPid={request.mstPid}, drafterId={request.drafterId}"
    )

    api_base_url = os.getenv(
        "APPROVAL_API_BASE_URL",
        "https://dev-api.ntoday.kr/api/v1/epaper",  # 기본 URL은 예시
    )
    endpoint = "myLine"
    url = f"{api_base_url}/{endpoint}"

    params = {"mstPid": request.mstPid, "drafterId": request.drafterId}
    headers = {"Content-Type": "application/json"}

    drafter_name = "정보 없음"  # API 응답에서 파싱하여 채울 예정
    drafter_department = "정보 없음"  # API 응답에서 파싱하여 채울 예정
    approvers_details = []
    response_message = "API 호출 중 오류 발생"
    response_code = 0  # 실패 시

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logging.info(f"외부 myLine API 호출: POST {url} with params: {params}")
            api_response = await client.post(url, json=params, headers=headers)
            api_response.raise_for_status()  # HTTP 4xx/5xx 오류 발생 시 예외 발생

            api_response_json = api_response.json()
            logging.info(f"외부 myLine API 응답: {api_response_json}")

            # API 응답 구조에 따라 파싱 로직을 조정해야 합니다.
            # 예시: 응답이 {"code": 1, "message": "...", "data": {"drafterName": "...", "drafterDepartment": "...", "approvers": [...]}} 형태라고 가정
            if api_response_json.get("code") == 1 and "data" in api_response_json:
                api_data = api_response_json["data"]

                # 기안자 정보 파싱 (실제 API 응답 필드명으로 변경 필요)
                drafter_name = api_data.get("drafterName", drafter_name)
                drafter_department = api_data.get(
                    "drafterDepartment", drafter_department
                )

                # 결재자 목록 파싱 (실제 API 응답 필드명 및 구조로 변경 필요)
                raw_approvers = api_data.get("approvers", [])
                if isinstance(raw_approvers, list):
                    for approver_item in raw_approvers:
                        approvers_details.append(
                            form_schema.ApproverDetail(  # form_schema 사용
                                aprvPsId=approver_item.get("aprvPsId", "N/A"),
                                aprvPsNm=approver_item.get("aprvPsNm", "N/A"),
                                aprvDvTy=approver_item.get("aprvDvTy", "N/A"),
                                ordr=approver_item.get("ordr", 0),
                            )
                        )
                response_message = api_response_json.get(
                    "message", "결재 라인 조회 성공"
                )
                response_code = 1  # 성공
            else:
                response_message = api_response_json.get(
                    "message", "API에서 유효한 데이터를 반환하지 않았습니다."
                )
                logging.warning(
                    f"외부 myLine API 응답 코드 또는 데이터 형식 오류: {api_response_json}"
                )

    except httpx.HTTPStatusError as e:
        response_message = (
            f"외부 myLine API HTTP 오류: {e.response.status_code} - {e.response.text}"
        )
        logging.error(response_message)
    except httpx.RequestError as e:
        response_message = f"외부 myLine API 요청 오류: {e}"
        logging.error(response_message)
    except json.JSONDecodeError as e:  # json 임포트 필요
        response_message = f"외부 myLine API 응답 JSON 파싱 오류: {e}"
        logging.error(response_message)
    except Exception as e:
        response_message = f"외부 myLine API 처리 중 예외 발생: {str(e)}"
        logging.error(response_message, exc_info=True)

    final_data = form_schema.ApproverInfoData(
        drafterName=drafter_name,
        drafterDepartment=drafter_department,
        approvers=approvers_details,
    )

    return form_schema.ApproverInfoResponse(
        code=response_code, message=response_message, data=final_data
    )


# --- END 외부 myLine API 직접 호출 엔드포인트 --- #


# --- 2단계: 폼 데이터 → API Payload 변환 엔드포인트 --- #
@app.post("/convert-form-to-payload")
async def convert_form_to_payload_endpoint(request: dict):
    """HTML 폼에서 받은 데이터를 최종 API Payload로 변환하는 엔드포인트"""
    try:
        form_type = request.get("form_type")
        form_data = request.get("form_data")

        if not form_type:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MISSING_FORM_TYPE",
                    "message": "form_type이 필요합니다.",
                },
            )

        if not form_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MISSING_FORM_DATA",
                    "message": "form_data가 필요합니다.",
                },
            )

        # 2단계 변환 로직 호출
        api_payload = convert_form_data_to_api_payload(form_type, form_data)

        return {"success": True, "form_type": form_type, "api_payload": api_payload}

    except ValueError as ve:
        # 지원하지 않는 양식 타입 등의 경우
        raise HTTPException(
            status_code=400, detail={"error": "INVALID_FORM_TYPE", "message": str(ve)}
        )
    except Exception as e:
        logging.error(f"폼 데이터 변환 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CONVERSION_ERROR",
                "message": "폼 데이터를 API Payload로 변환하는 중 오류가 발생했습니다.",
            },
        )


# --- 최종 API 제출 엔드포인트 --- #
@app.post("/submit-form")
async def submit_form_endpoint(request: dict):
    """변환된 API Payload를 실제 외부 API로 제출하는 엔드포인트"""
    try:
        form_type = request.get("form_type")
        form_data = request.get("form_data")

        if not form_type or not form_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MISSING_DATA",
                    "message": "form_type과 form_data가 필요합니다.",
                },
            )

        # 1단계: 폼 데이터를 API Payload로 변환
        api_payload = convert_form_data_to_api_payload(form_type, form_data)

        # 2단계: 외부 API로 제출
        api_base_url = os.getenv(
            "APPROVAL_API_BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper"
        )

        # 모든 양식에 대해 동일한 엔드포인트 사용
        endpoint = "register"  # 실제 외부 API에서 사용하는 통합 엔드포인트
        submit_url = f"{api_base_url}/{endpoint}"

        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            logging.info(f"외부 API 제출: POST {submit_url}")
            logging.info(f"Payload: {api_payload}")

            api_response = await client.put(
                submit_url, json=api_payload, headers=headers
            )

            api_response.raise_for_status()
            response_data = api_response.json()

            logging.info(f"외부 API 응답: {response_data}")

            return {
                "success": True,
                "form_type": form_type,
                "api_response": response_data,
                "submitted_payload": api_payload,
            }

    except httpx.HTTPStatusError as e:
        error_detail = f"외부 API 오류: {e.response.status_code}"
        try:
            error_response = e.response.json()
            error_detail += f" - {error_response}"
        except:
            error_detail += f" - {e.response.text}"

        logging.error(error_detail)
        raise HTTPException(
            status_code=502,
            detail={
                "error": "EXTERNAL_API_ERROR",
                "message": "외부 API 호출 중 오류가 발생했습니다.",
                "details": error_detail,
            },
        )
    except httpx.RequestError as e:
        logging.error(f"외부 API 요청 오류: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "API_REQUEST_ERROR",
                "message": "외부 API 연결 중 오류가 발생했습니다.",
            },
        )
    except Exception as e:
        logging.error(f"양식 제출 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SUBMISSION_ERROR",
                "message": "양식 제출 중 오류가 발생했습니다.",
            },
        )


# --- END 2단계 변환 및 제출 엔드포인트 --- #


# FastAPI 엔트리포인트 및 라우터 정의 예정
