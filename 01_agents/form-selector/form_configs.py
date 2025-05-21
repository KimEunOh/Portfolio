from typing import Dict, Type
from pydantic import BaseModel

from .schema import (
    AnnualLeaveSlots,
    BusinessTripSlots,
    MeetingExpenseSlots,
    OtherExpenseSlots,
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


FORM_CONFIGS: Dict[str, FormConfig] = {
    "연차 신청서": FormConfig(
        model=AnnualLeaveSlots,
        prompt_template_path="prompts/annual_leave_slots_prompt.txt",
        html_template_path="templates/annual_leave.html",
    ),
    "출장 신청서": FormConfig(
        model=BusinessTripSlots,
        prompt_template_path="prompts/business_trip_slots_prompt.txt",
        html_template_path="templates/business_trip.html",
    ),
    "회의비 지출결의서": FormConfig(
        model=MeetingExpenseSlots,
        prompt_template_path="prompts/meeting_expense_slots_prompt.txt",
        html_template_path="templates/meeting_expense.html",
    ),
    "기타 지출결의서": FormConfig(
        model=OtherExpenseSlots,
        prompt_template_path="prompts/other_expense_slots_prompt.txt",
        html_template_path="templates/other_expense.html",
    ),
    "야근식대비용 신청서": FormConfig(
        model=DinnerExpenseSlots,
        prompt_template_path="prompts/dinner_expense_slots_prompt.txt",
        html_template_path="templates/dinner_expense.html",
    ),
    "교통비 신청서": FormConfig(
        model=TransportationExpenseSlots,
        prompt_template_path="prompts/transportation_expense_slots_prompt.txt",
        html_template_path="templates/transportation_expense.html",
    ),
    "파견 및 출장 보고서": FormConfig(
        model=DispatchBusinessTripReportSlots,
        prompt_template_path="prompts/dispatch_businesstrip_report_slots_prompt.txt",
        html_template_path="templates/dispatch_businesstrip_report.html",
    ),
    "비품/소모품 구입내역서": FormConfig(
        model=InventoryPurchaseReportSlots,
        prompt_template_path="prompts/inventory_purchase_report_slots_prompt.txt",
        html_template_path="templates/inventory_purchase_report.html",
    ),
    "구매 품의서": FormConfig(
        model=PurchaseApprovalFormSlots,
        prompt_template_path="prompts/purchase_approval_form_slots_prompt.txt",
        html_template_path="templates/purchase_approval_form.html",
    ),
    "개인 경비 사용 내역서": FormConfig(
        model=PersonalExpenseReportSlots,
        prompt_template_path="prompts/personal_expense_report_slots_prompt.txt",
        html_template_path="templates/personal_expense_report.html",
    ),
    "법인카드 지출내역서": FormConfig(
        model=CorporateCardStatementSlots,
        prompt_template_path="prompts/corporate_card_statement_slots_prompt.txt",
        html_template_path="templates/corporate_card_statement.html",
    ),
}

# 사용 가능한 양식 이름 목록
AVAILABLE_FORM_TYPES = list(FORM_CONFIGS.keys())
