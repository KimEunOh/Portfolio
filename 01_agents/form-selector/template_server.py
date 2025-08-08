from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os


app = FastAPI(title="Template Server", version="1.0.0")


# 정적 파일 마운트 (/ui → static)
app.mount(
    "/ui",
    StaticFiles(
        directory=os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
    ),
    name="static",
)

# publishing HTML 원본 보기
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
}


def _inject_base_href(html: str, base_href: str) -> str:
    try:
        lower = html.lower()
        idx = lower.find("<head")
        if idx != -1:
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
        head_assets = "\n".join(
            [
                # CSS
                '<link rel="stylesheet" href="/ui/publish/plugins/jquery/jquery-ui-1.14.1.min.css">',
                '<link rel="stylesheet" href="/ui/publish/plugins/datetimepicker/jquery.datetimepicker.min.css">',
                '<link rel="stylesheet" href="/ui/publish/plugins/dropzone/dropzone.min.css">',
                # 메인 스타일(정확 경로: /ui/publish/scss/style.min.css)
                '<link rel="stylesheet" href="/ui/publish/scss/style.min.css">',
                # 안전한 fallback
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
                # External integration (COMMON → ADAPTER → page script)
                '<script src="/ui/js/external/common/slots.js"></script>',
                '<script src="/ui/js/external/common/approver.js"></script>',
                '<script src="/ui/js/external/adapters/annual_leave.js"></script>',
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
    """templates/publishing 안의 HTML을 열어 <head> 리소스를 자동 주입해 반환한다."""
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
    """사내 API 스타일 엔드포인트로 publishing 템플릿을 반환한다."""
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
