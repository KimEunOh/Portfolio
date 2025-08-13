from typing import Dict, Type, Optional
import os
from form_selector.core.config import get_settings
from pydantic import BaseModel

from .schema import (
    AnnualLeaveSlots,
    DinnerExpenseSlots,
    TransportationExpenseSlots,
    DispatchBusinessTripReportSlots,
    InventoryPurchaseReportSlots,
    PurchaseApprovalFormSlots,
    PersonalExpenseReportSlots,
    CorporateCardStatementSlots,
    ResignationLetterSlots,
)


class FormConfig(BaseModel):
    model: Type[BaseModel]
    prompt_template_path: str
    html_template_path: str  # 로컬 경로 또는 외부 API URL 모두 지원
    mstPid: int
    english_id: str  # 백엔드 API에서 사용할 영어 식별자
    items_config: Optional[Dict[str, str]] = None  # 아이템 리스트 설정을 위한 필드 추가
    is_external_template: bool = False  # 외부 API 여부 플래그 추가


# REST 템플릿 베이스 URL (없으면 로컬 FastAPI 기본값)
FORM_TEMPLATE_BASE_URL = get_settings().FORM_TEMPLATE_BASE_URL


def build_rest_template_url(mst_pid: int) -> str:
    return f"{FORM_TEMPLATE_BASE_URL}/api/v1/o/form/master/{mst_pid}"


FORM_CONFIGS: Dict[str, FormConfig] = {
    "연차 신청서": FormConfig(
        model=AnnualLeaveSlots,
        prompt_template_path="annual_leave_slots_prompt.txt",
        html_template_path=build_rest_template_url(1),
        mstPid=1,
        english_id="annual_leave",
        is_external_template=True,  # 로컬 REST 템플릿 사용
    ),
    "야근식대비용 신청서": FormConfig(
        model=DinnerExpenseSlots,
        prompt_template_path="dinner_expense_slots_prompt.txt",
        html_template_path=build_rest_template_url(3),
        mstPid=3,
        english_id="dinner_expense",
        is_external_template=True,
    ),
    "교통비 신청서": FormConfig(
        model=TransportationExpenseSlots,
        prompt_template_path="transportation_expense_slots_prompt.txt",
        html_template_path=build_rest_template_url(4),
        mstPid=4,
        english_id="transportation_expense",
        is_external_template=True,
    ),
    "파견 및 출장 보고서": FormConfig(
        model=DispatchBusinessTripReportSlots,
        prompt_template_path="dispatch_businesstrip_report_slots_prompt.txt",
        html_template_path=build_rest_template_url(5),
        mstPid=5,
        english_id="dispatch_businesstrip_report",
        is_external_template=True,
    ),
    "비품/소모품 구입내역서": FormConfig(
        model=InventoryPurchaseReportSlots,
        prompt_template_path="inventory_purchase_report_slots_prompt.txt",
        html_template_path=build_rest_template_url(6),
        mstPid=6,
        english_id="inventory_purchase_report",
        # 충돌 방지: hidden 배열 키를 purchase_items로 표준화
        items_config={"list_key": "purchase_items", "date_key": "request_date"},
        is_external_template=True,
    ),
    "구매 품의서": FormConfig(
        model=PurchaseApprovalFormSlots,
        prompt_template_path="purchase_approval_form_slots_prompt.txt",
        html_template_path=build_rest_template_url(7),
        mstPid=7,
        english_id="purchase_approval_form",
        items_config={"list_key": "items", "date_key": "item_delivery_request_date"},
        is_external_template=True,
    ),
    "개인 경비 사용내역서": FormConfig(
        model=PersonalExpenseReportSlots,
        prompt_template_path="personal_expense_report_slots_prompt.txt",
        html_template_path=build_rest_template_url(8),
        mstPid=8,
        english_id="personal_expense_report",
        items_config={"list_key": "expense_items", "date_key": "expense_date"},
        is_external_template=True,
    ),
    "법인카드 지출내역서": FormConfig(
        model=CorporateCardStatementSlots,
        prompt_template_path="corporate_card_statement_slots_prompt.txt",
        html_template_path=build_rest_template_url(9),
        mstPid=9,
        english_id="corporate_card_statement",
        items_config={"list_key": "card_usage_items", "date_key": "usage_date"},
        is_external_template=True,
    ),
}

# 외부 API URL 예시 (주석 처리)
# 외부 API를 사용하려면 위의 html_template_path를 URL로 변경하고 is_external_template을 True로 설정하세요.
# 예시:
# "연차 신청서": FormConfig(
#     model=AnnualLeaveSlots,
#     prompt_template_path="annual_leave_slots_prompt.txt",
#     html_template_path="https://api.example.com/templates/annual_leave.html",
#     mstPid=1,
#     english_id="annual_leave",
#     is_external_template=True,  # 외부 API 플래그
# ),

# 사용 가능한 양식 이름 목록
AVAILABLE_FORM_TYPES = list(FORM_CONFIGS.keys())

# RAG 검색 시 HTML 템플릿 파일명을 form_type으로 조회하기 위한 맵
# 예: "연차 신청서" -> "annual_leave.html"
TEMPLATE_FILENAME_MAP = {
    form_name: config.html_template_path for form_name, config in FORM_CONFIGS.items()
}

# 한국어 양식명 → 영어 식별자 자동 매핑 생성
# 예: "야근식대비용 신청서" -> "dinner_expense"
KOREAN_TO_ENGLISH_MAP = {
    form_name: config.english_id for form_name, config in FORM_CONFIGS.items()
}

# 영어 식별자 → 한국어 양식명 역방향 매핑
# 예: "dinner_expense" -> "야근식대비용 신청서"
ENGLISH_TO_KOREAN_MAP = {
    config.english_id: form_name for form_name, config in FORM_CONFIGS.items()
}


def get_english_form_type(korean_form_type: str) -> str:
    """한국어 양식명을 영어 식별자로 변환

    Args:
        korean_form_type: 한국어 양식명 (예: "야근식대비용 신청서")

    Returns:
        str: 영어 식별자 (예: "dinner_expense")

    Raises:
        ValueError: 지원하지 않는 양식 타입인 경우
    """
    if korean_form_type in KOREAN_TO_ENGLISH_MAP:
        return KOREAN_TO_ENGLISH_MAP[korean_form_type]

    # 이미 영어 식별자인 경우 그대로 반환
    if korean_form_type in ENGLISH_TO_KOREAN_MAP:
        return korean_form_type

    raise ValueError(f"Unsupported form type: {korean_form_type}")


def get_korean_form_type(english_form_type: str) -> str:
    """영어 식별자를 한국어 양식명으로 변환

    Args:
        english_form_type: 영어 식별자 (예: "dinner_expense")

    Returns:
        str: 한국어 양식명 (예: "야근식대비용 신청서")

    Raises:
        ValueError: 지원하지 않는 양식 타입인 경우
    """
    if english_form_type in ENGLISH_TO_KOREAN_MAP:
        return ENGLISH_TO_KOREAN_MAP[english_form_type]

    # 이미 한국어 양식명인 경우 그대로 반환
    if english_form_type in KOREAN_TO_ENGLISH_MAP:
        return english_form_type

    raise ValueError(f"Unsupported form type: {english_form_type}")


if __name__ == "__main__":
    print("--- 사용 가능한 양식 종류 ---")
    for form_type in AVAILABLE_FORM_TYPES:
        print(form_type)

    print("\n--- 양식 설정 정보 ---")
    for form_name, config in FORM_CONFIGS.items():
        print(f"양식명: {form_name}")
        print(f"  Pydantic 모델: {config.model.__name__}")
        print(f"  프롬프트 파일: {config.prompt_template_path}")
        print(f"  HTML 템플릿 파일: {config.html_template_path}")

    print("\n--- 템플릿 파일명 맵 ---")
    print(TEMPLATE_FILENAME_MAP)
