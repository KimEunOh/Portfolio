from typing import Dict, Type
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
)


class FormConfig(BaseModel):
    model: Type[BaseModel]
    prompt_template_path: str
    html_template_path: str
    mstPid: int


FORM_CONFIGS: Dict[str, FormConfig] = {
    "연차 신청서": FormConfig(
        model=AnnualLeaveSlots,
        prompt_template_path="annual_leave_slots_prompt.txt",
        html_template_path="templates/annual_leave.html",
        mstPid=1,
    ),
    "야근식대비용 신청서": FormConfig(
        model=DinnerExpenseSlots,
        prompt_template_path="dinner_expense_slots_prompt.txt",
        html_template_path="templates/dinner_expense.html",
        mstPid=2,
    ),
    "교통비 신청서": FormConfig(
        model=TransportationExpenseSlots,
        prompt_template_path="transportation_expense_slots_prompt.txt",
        html_template_path="templates/transportation_expense.html",
        mstPid=3,
    ),
    "파견 및 출장 보고서": FormConfig(
        model=DispatchBusinessTripReportSlots,
        prompt_template_path="dispatch_businesstrip_report_slots_prompt.txt",
        html_template_path="templates/dispatch_businesstrip_report.html",
        mstPid=4,
    ),
    "비품/소모품 구입내역서": FormConfig(
        model=InventoryPurchaseReportSlots,
        prompt_template_path="inventory_purchase_report_slots_prompt.txt",
        html_template_path="templates/inventory_purchase_report.html",
        mstPid=5,
    ),
    "구매 품의서": FormConfig(
        model=PurchaseApprovalFormSlots,
        prompt_template_path="purchase_approval_form_slots_prompt.txt",
        html_template_path="templates/purchase_approval_form.html",
        mstPid=6,
    ),
    "개인 경비 사용 내역서": FormConfig(
        model=PersonalExpenseReportSlots,
        prompt_template_path="personal_expense_report_slots_prompt.txt",
        html_template_path="templates/personal_expense_report.html",
        mstPid=7,
    ),
    "법인카드 지출내역서": FormConfig(
        model=CorporateCardStatementSlots,
        prompt_template_path="corporate_card_statement_slots_prompt.txt",
        html_template_path="templates/corporate_card_statement.html",
        mstPid=8,
    ),
}

# 사용 가능한 양식 이름 목록
AVAILABLE_FORM_TYPES = list(FORM_CONFIGS.keys())

# RAG 검색 시 HTML 템플릿 파일명을 form_type으로 조회하기 위한 맵
# 예: "연차 신청서" -> "annual_leave.html"
TEMPLATE_FILENAME_MAP = {
    form_name: config.html_template_path for form_name, config in FORM_CONFIGS.items()
}

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
