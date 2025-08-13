# requirements.txt에 다음 패키지 포함 필요:
# fastapi, uvicorn, langchain, langchain_openai, pydantic

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from form_selector.schema import UserInput
from form_selector.service import classify_and_extract_slots_for_template
import os
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
import httpx
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
from urllib.parse import urlparse

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

# CORS 설정 (외부 템플릿 서버에서 메인 서버로 제출 가능하도록)
ALLOWED_CORS_ORIGINS = os.getenv(
    "ALLOWED_CORS_ORIGINS",
    "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000,null",
)
_origins = [o.strip() for o in ALLOWED_CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 마운트 (static 폴더를 /ui 경로로 접근 가능하게 함)
# HTML, CSS, JS 파일들을 static 폴더에 위치시킵니다.
app.mount(
    "/ui",
    StaticFiles(
        directory=os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
    ),
    name="static",
)

# 정적 템플릿 미리보기용 마운트 (publishing HTML들을 그대로 파일로 제공)
app.mount(
    "/publishing",
    StaticFiles(
        directory=os.path.abspath(
            os.path.join(os.path.dirname(__file__), "templates", "publishing")
        )
    ),
    name="publishing",
)

# mstPid → publishing HTML 파일명 매핑
MSTPID_TO_PUBLISHING_FILENAME = {
    1: "annualLeaveForm.html",  # 연차 신청서
    3: "overTimeDinnerForm.html",  # 야근식대비용 신청서
    4: "transPortFeeForm.html",  # 교통비 신청서
    5: "dispatchForm.html",  # 파견 및 출장 보고서
    6: "purchaseEquipForm.html",  # 비품/소모품 구입내역서
    7: "purchaseRequestForm.html",  # 구매 품의서
    8: "personalExpenseForm.html",  # 개인 경비 사용 내역서
    9: "corCreditCardForm.html",  # 법인카드 지출내역서
    # 10(사직서)는 publishing 템플릿 없음
}


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


# ================== 외부 양식 프록시 렌더링 (치환 + iframe용) ==================


class ExternalFormRequest(BaseModel):
    form_type: str
    slots: Dict[str, Any] = {}
    approver_info: Optional[Dict[str, Any]] = None
    drafter_id: Optional[str] = None


def _inject_base_href(html: str, base_href: str) -> str:
    try:
        lower = html.lower()
        idx = lower.find("<head")
        if idx != -1:
            # 첫 <head> 태그의 끝을 찾아 간단히 삽입
            close_idx = lower.find(">", idx)
            if close_idx != -1:
                return (
                    html[: close_idx + 1]
                    + f'\n<base href="{base_href}">'
                    + html[close_idx + 1 :]
                )
        return f'<base href="{base_href}">' + html
    except Exception:
        return html


def _inject_head_assets(html: str) -> str:
    """publishing HTML의 <head>에 필요한 CSS/JS를 삽입하고, Thymeleaf head 조각을 제거한다."""
    try:
        # 1) Thymeleaf head 조각 제거
        html = html.replace(
            '<th:block th:insert="~{/soulGod/fragments/headChatbot :: headChatbot}"></th:block>',
            "",
        )

        # 2) 필요한 리소스 태그 구성 (정적 /ui/publish 경로 사용)
        submit_base = os.getenv("SUBMIT_API_BASE_URL", "http://localhost:8000")
        head_assets = "\n".join(
            [
                # CSS
                '<link rel="stylesheet" href="/ui/publish/plugins/jquery/jquery-ui-1.14.1.min.css">',
                '<link rel="stylesheet" href="/ui/publish/plugins/datetimepicker/jquery.datetimepicker.min.css">',
                '<link rel="stylesheet" href="/ui/publish/plugins/dropzone/dropzone.min.css">',
                # 메인 스타일(정확 경로: /ui/publish/scss/style.min.css)
                '<link rel="stylesheet" href="/ui/publish/scss/style.min.css">',
                # 안전한 fallback (개발환경에서 min 파일이 없을 때 대비)
                '<link rel="stylesheet" href="/ui/publish/scss/style.css">',
                # JS (jQuery → jQuery UI → plugins → app js)
                '<script src="/ui/publish/plugins/jquery/jquery-3.7.1.min.js"></script>',
                '<script src="/ui/publish/plugins/jquery/jquery-ui-1.14.1.min.js"></script>',
                '<script src="/ui/publish/plugins/jquery.nice-select.min.js"></script>',
                '<script src="/ui/publish/plugins/datetimepicker/jquery.datetimepicker.full.min.js"></script>',
                '<script src="/ui/publish/plugins/dropzone/dropzone.min.js"></script>',
                '<script src="/ui/publish/plugins/jquery.inputmask.bundle.js"></script>',
                '<script src="/ui/publish/js/dropzone.js"></script>',
                '<script src="/ui/publish/js/style.js"></script>',
                # 제출 API 베이스 (빈 문자열이면 동일 오리진)
                f'<script>window.__FORM_SUBMIT_BASE__="{submit_base}";</script>',
                # External integration for autofill/approver rendering + common submit
                '<script src="/ui/js/external/common/slots.js"></script>',
                '<script src="/ui/js/external/common/approver.js"></script>',
                '<script src="/ui/js/external/common/ui_reinit.js"></script>',
                '<script src="/ui/js/external/common/submit.js"></script>',
                '<script src="/ui/js/external/adapters/annual_leave.js"></script>',
                '<script src="/ui/js/external/adapters/dinner_expense.js"></script>',
                '<script src="/ui/js/external/adapters/transportation_expense.js"></script>',
                '<script src="/ui/js/external/adapters/dispatch_businesstrip_report.js"></script>',
                '<script src="/ui/js/external/adapters/inventory_purchase_report.js"></script>',
                '<script src="/ui/js/external/adapters/purchase_approval_form.js"></script>',
                '<script src="/ui/js/external/adapters/personal_expense_report.js"></script>',
                '<script src="/ui/js/external/adapters/corporate_card_statement.js"></script>',
                '<script src="/ui/js/external/adapters/adapter_bootstrap.js"></script>',
                # 초기화 스크립트 (선택/입력 UI 활성화)
                '<script>document.addEventListener("DOMContentLoaded",function(){try{if(typeof niceSelect==="function"){niceSelect("body");}}catch(e){} try{if(typeof inputActive==="function"){inputActive("body");}}catch(e){}});</script>',
            ]
        )

        # 3) <head> 바로 뒤에 삽입. <base>도 함께 두면 상대경로 안정성↑
        injected = _inject_base_href(html, base_href="/ui/")
        lower = injected.lower()
        idx = lower.find("<head")
        if idx != -1:
            close_idx = lower.find(">", idx)
            if close_idx != -1:
                return (
                    injected[: close_idx + 1]
                    + "\n"
                    + head_assets
                    + "\n"
                    + injected[close_idx + 1 :]
                )
        # <head>가 없으면 문서 맨 앞에 최대한 안전하게 삽입
        return head_assets + "\n" + injected
    except Exception:
        return html


@app.get("/publishing-render/{file_path:path}", response_class=HTMLResponse)
async def render_publishing_html(file_path: str):
    """templates/publishing 안의 HTML을 열어 <head> 리소스를 자동 주입해 반환한다.

    사용 예: /publishing-render/annualLeaveForm.html
    """
    try:
        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "templates", "publishing")
        )
        # 디렉토리 탈출 방지
        target_path = os.path.abspath(os.path.join(base_dir, file_path))
        if not target_path.startswith(base_dir):
            raise HTTPException(status_code=403, detail={"error": "FORBIDDEN"})

        if not os.path.exists(target_path) or not os.path.isfile(target_path):
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND"})

        with open(target_path, "r", encoding="utf-8") as f:
            html = f.read()

        html = _inject_head_assets(html)
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "RENDER_FAILED", "message": str(e)}
        )


@app.get("/api/v1/o/form/master/{mstPid}", response_class=HTMLResponse)
async def render_publishing_by_mstpid(mstPid: int):
    """사내 API 스타일 엔드포인트로 publishing 템플릿을 반환한다.

    예: /api/v1/o/form/master/1 → annualLeaveForm.html의 리소스 주입 버전
    """
    try:
        filename = MSTPID_TO_PUBLISHING_FILENAME.get(mstPid)
        if not filename:
            raise HTTPException(
                status_code=404, detail={"error": "UNKNOWN_MSTPID", "mstPid": mstPid}
            )

        base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "templates", "publishing")
        )
        target_path = os.path.abspath(os.path.join(base_dir, filename))
        if not os.path.exists(target_path) or not os.path.isfile(target_path):
            raise HTTPException(
                status_code=404, detail={"error": "NOT_FOUND", "file": filename}
            )

        with open(target_path, "r", encoding="utf-8") as f:
            html = f.read()

        html = _inject_head_assets(html)
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "RENDER_FAILED", "message": str(e)}
        )


def _build_fill_script(
    slots: Dict[str, Any], approver_info: Optional[Dict[str, Any]] = None
) -> str:
    slots_json = json.dumps(slots, ensure_ascii=False).replace(
        "</script>", "<\\/script>"
    )
    approver_json = json.dumps(approver_info or {}, ensure_ascii=False).replace(
        "</script>", "<\\/script>"
    )
    script = """
<script>
(function(){
  window.__FORM_SLOTS__ = __SLOTS_JSON__;
  window.__APPROVER_INFO__ = __APPROVER_JSON__;

  function getEnglishFormType(){
    try{
      if(window.__FORM_SLOTS__ && window.__FORM_SLOTS__.form_type){ return String(window.__FORM_SLOTS__.form_type); }
    }catch(e){}
    // heuristic by path
    try{
      var path = (window.location.pathname||'').toLowerCase();
      if(/master\/1\b/.test(path)) return 'annual_leave';
      if(/master\/3\b/.test(path)) return 'dinner_expense';
      if(/master\/4\b/.test(path)) return 'transportation_expense';
      if(/master\/5\b/.test(path)) return 'dispatch_businesstrip_report';
      if(/master\/6\b/.test(path)) return 'inventory_purchase_report';
      if(/master\/7\b/.test(path)) return 'purchase_approval_form';
      if(/master\/8\b/.test(path)) return 'personal_expense_report';
      if(/master\/9\b/.test(path)) return 'corporate_card_statement';
    }catch(e){}
    return null;
  }

  function tryBootstrap(){
    try{
      // 1) 우선 adapter-bootstrap이 있다면 그쪽 자동 감지 로직에 위임
      if (window.UIReinit && window.UIReinit.schedule){ try{ window.UIReinit.schedule(); }catch(_e){} }
      var ft = getEnglishFormType();
      if (ft === 'annual_leave' && window.AnnualLeaveAdapter && typeof window.AnnualLeaveAdapter.bootstrap === 'function'){
        window.AnnualLeaveAdapter.bootstrap(window.__FORM_SLOTS__ || {}, window.__APPROVER_INFO__ || {});
        return true;
      }
      if (ft === 'dinner_expense' && window.DinnerExpenseAdapter && typeof window.DinnerExpenseAdapter.bootstrap === 'function'){
        window.DinnerExpenseAdapter.bootstrap(window.__FORM_SLOTS__ || {}, window.__APPROVER_INFO__ || {});
        return true;
      }
      if (ft === 'transportation_expense' && window.TransportationExpenseAdapter && typeof window.TransportationExpenseAdapter.bootstrap === 'function'){
        window.TransportationExpenseAdapter.bootstrap(window.__FORM_SLOTS__ || {}, window.__APPROVER_INFO__ || {});
        return true;
      }
      return false;
    }catch(e){ return false; }
  }

  function startAttempts(){
    var attempts = 0;
    var timer = setInterval(function(){
      attempts++;
      if (tryBootstrap() || attempts > 20){ clearInterval(timer); }
    }, 150);
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', startAttempts);
  } else {
    startAttempts();
  }
})();
</script>
"""
    return script.replace("__SLOTS_JSON__", slots_json).replace(
        "__APPROVER_JSON__", approver_json
    )


@app.post("/external-form", response_class=HTMLResponse)
async def render_external_form(req: ExternalFormRequest):
    try:
        from form_selector.form_configs import FORM_CONFIGS

        form_type = req.form_type
        config = FORM_CONFIGS.get(form_type)
        if not config:
            raise HTTPException(
                status_code=400,
                detail={"error": "UNKNOWN_FORM_TYPE", "message": form_type},
            )
        template_url = config.html_template_path
        if not (
            isinstance(template_url, str)
            and template_url.startswith(("http://", "https://"))
        ):
            raise HTTPException(
                status_code=400, detail={"error": "NOT_EXTERNAL_TEMPLATE"}
            )

        # 2.1) 외부 템플릿 가져오기 (실패 시 로컬 퍼블리싱 템플릿으로 폴백)
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(template_url)
                resp.raise_for_status()
                html = resp.text
        except httpx.RequestError:
            # 폴백: 로컬 퍼블리싱 템플릿 사용 (개발/오프라인 환경 대비)
            try:
                from pathlib import Path

                filename = MSTPID_TO_PUBLISHING_FILENAME.get(config.mstPid)
                if not filename:
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error": "TEMPLATE_FETCH_FAILED",
                            "message": f"External fetch failed and no local filename for mstPid {config.mstPid}",
                        },
                    )
                base_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "templates", "publishing")
                )
                target_path = os.path.abspath(os.path.join(base_dir, filename))
                if not (os.path.exists(target_path) and os.path.isfile(target_path)):
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "error": "TEMPLATE_FETCH_FAILED",
                            "message": f"External fetch failed and local file not found: {filename}",
                        },
                    )
                with open(target_path, "r", encoding="utf-8") as f:
                    html = f.read()
            except HTTPException:
                raise
            except Exception as _e:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error": "TEMPLATE_FETCH_FAILED",
                        "message": f"External fetch failed and local fallback errored: {_e}",
                    },
                )

        parsed = urlparse(template_url)
        base_href = f"{parsed.scheme}://{parsed.netloc}/"

        # 1) 외부 호스트 기준 base href 유지 (원본 상대경로 보존)
        html_with_base = _inject_base_href(html, base_href)

        # 2) 필요한 head 자산 주입 (base 재삽입 없이, 동일 오리진 /ui 자산 사용)
        submit_base = os.getenv("SUBMIT_API_BASE_URL", "http://localhost:8000")
        head_assets = "\n".join(
            [
                '<link rel="stylesheet" href="/ui/publish/plugins/jquery/jquery-ui-1.14.1.min.css">',
                '<link rel="stylesheet" href="/ui/publish/plugins/datetimepicker/jquery.datetimepicker.min.css">',
                '<link rel="stylesheet" href="/ui/publish/plugins/dropzone/dropzone.min.css">',
                '<link rel="stylesheet" href="/ui/publish/scss/style.min.css">',
                '<link rel="stylesheet" href="/ui/publish/scss/style.css">',
                '<script src="/ui/publish/plugins/jquery/jquery-3.7.1.min.js"></script>',
                '<script src="/ui/publish/plugins/jquery/jquery-ui-1.14.1.min.js"></script>',
                '<script src="/ui/publish/plugins/jquery.nice-select.min.js"></script>',
                '<script src="/ui/publish/plugins/datetimepicker/jquery.datetimepicker.full.min.js"></script>',
                '<script src="/ui/publish/plugins/dropzone/dropzone.min.js"></script>',
                '<script src="/ui/publish/plugins/jquery.inputmask.bundle.js"></script>',
                '<script src="/ui/publish/js/dropzone.js"></script>',
                '<script src="/ui/publish/js/style.js"></script>',
                f'<script>window.__FORM_SUBMIT_BASE__="{submit_base}";</script>',
                '<script src="/ui/js/external/common/slots.js"></script>',
                '<script src="/ui/js/external/common/approver.js"></script>',
                '<script src="/ui/js/external/common/ui_reinit.js"></script>',
                '<script src="/ui/js/external/common/submit.js"></script>',
                '<script src="/ui/js/external/adapters/annual_leave.js"></script>',
                '<script src="/ui/js/external/adapters/dinner_expense.js"></script>',
                '<script src="/ui/js/external/adapters/transportation_expense.js"></script>',
                '<script src="/ui/js/external/adapters/dispatch_businesstrip_report.js"></script>',
                '<script src="/ui/js/external/adapters/inventory_purchase_report.js"></script>',
                '<script src="/ui/js/external/adapters/purchase_approval_form.js"></script>',
                '<script src="/ui/js/external/adapters/personal_expense_report.js"></script>',
                '<script src="/ui/js/external/adapters/corporate_card_statement.js"></script>',
                '<script src="/ui/js/external/adapters/adapter_bootstrap.js"></script>',
                '<script>document.addEventListener("DOMContentLoaded",function(){try{if(typeof niceSelect==="function"){niceSelect("body");}}catch(e){} try{if(typeof inputActive==="function"){inputActive("body");}}catch(e){} try{ if(window.UIReinit){ window.UIReinit.schedule(); } }catch(e){} });</script>',
            ]
        )

        html_augmented = html_with_base
        if "</head>" in html_augmented:
            html_augmented = html_augmented.replace(
                "</head>", f"\n{head_assets}\n</head>"
            )
        else:
            html_augmented = head_assets + html_augmented

        # 3) 데이터 전역 주입 및 어댑터 부트스트랩
        # 외부 추천 플로우에서는 /master/{pid} 경로가 없어 mstPid가 비는 경우가 있어 슬롯에 주입
        effective_slots = dict(req.slots or {})
        try:
            effective_slots.setdefault("mstPid", config.mstPid)
            effective_slots.setdefault("mst_pid", config.mstPid)
            effective_slots.setdefault("form_type", config.english_id)
            # approver_info에 drafterId가 있으면 전역 부트스트랩 데이터에도 반영되도록 슬롯에 힌트 추가
            if req.approver_info and isinstance(req.approver_info, dict):
                di = req.approver_info.get("drafterId") or req.approver_info.get(
                    "drafter_id"
                )
                if di:
                    effective_slots.setdefault("drafterId", di)
                    effective_slots.setdefault("drafter_id", di)
            # 요청 본문에 drafter_id가 오면 우선 반영
            if req.drafter_id:
                effective_slots["drafterId"] = req.drafter_id
                effective_slots["drafter_id"] = req.drafter_id
        except Exception:
            pass
        lower = html_augmented.lower()
        if "</body>" in lower:
            idx = lower.rfind("</body>")
            html_filled = (
                html_augmented[:idx]
                + _build_fill_script(effective_slots, req.approver_info)
                + html_augmented[idx:]
            )
        else:
            html_filled = html_augmented + _build_fill_script(
                effective_slots, req.approver_info
            )

        return HTMLResponse(content=html_filled)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail={"error": "FETCH_FAILED", "message": e.response.text},
        )
    except Exception as e:
        logging.exception("External form render failed")
        raise HTTPException(
            status_code=500, detail={"error": "RENDER_FAILED", "message": str(e)}
        )
