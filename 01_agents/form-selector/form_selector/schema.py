from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class UserInput(BaseModel):
    input: str
    # user_id: Optional[str] = None # 사용자 식별자, 필요시 추가
    # session_id: Optional[str] = None # 세션 식별자, 필요시 추가


# 1단계: 양식 분류 모델의 출력 스키마
class FormClassifierOutput(BaseModel):
    form_type: str = Field(..., description="분류된 양식의 종류")
    keywords: Optional[List[str]] = Field(
        default_factory=list, description="추출된 키워드 리스트"
    )


# 2단계: 양식별 슬롯 추출 모델의 출력 스키마들
class AnnualLeaveSlots(BaseModel):
    """연차 신청서 슬롯"""

    leave_type: Optional[str] = Field(
        default=None,
        description="휴가 종류 (예: 연차, 오전 반차, 오후 반차, 오전 반반차, 오후 반반차)",
    )
    start_date: Optional[str] = Field(
        default=None, description="휴가 시작일 (YYYY-MM-DD 형식)"
    )
    end_date: Optional[str] = Field(
        default=None, description="휴가 종료일 (YYYY-MM-DD 형식)"
    )
    reason: Optional[str] = Field(default=None, description="휴가 사유")
    duration: Optional[str] = Field(
        default=None, description="휴가 기간 (자연어 표현, 예: 3일, 반나절, 하루)"
    )
    leave_days: Optional[str] = Field(
        default=None, description="연차 일수 (숫자로 표현된 일수, 예: 1, 0.5, 0.25)"
    )
    # applicant_name: Optional[str] = Field(default=None, description="신청자 이름")
    # department: Optional[str] = Field(default=None, description="신청자 부서")


class DinnerExpenseSlots(BaseModel):
    """야근식대비용 신청서 슬롯"""

    title: Optional[str] = Field(
        default=None, description="문서의 제목, 예: 야근식대비용 신청"
    )
    # applicant_team: Optional[str] = Field(
    #     default=None, description="신청자의 팀 또는 부서명 (API 연동 예정)"
    # )
    # applicant_name: Optional[str] = Field(default=None, description="신청자의 성명 (API 연동 예정)")
    # employee_id: Optional[str] = Field(default=None, description="신청자의 사번 (API 연동 예정)")
    # position: Optional[str] = Field(default=None, description="신청자의 직위 (API 연동 예정)")
    # contact_number: Optional[str] = Field(
    #     default=None, description="신청자의 연락처 (핸드폰 번호) (API 연동 예정)"
    # )
    application_date: Optional[str] = Field(
        default=None,
        description="신청일 (YYYY-MM-DD 형식으로 변환될 자연어 날짜, 예: 오늘, 2023-11-25)",
    )
    work_details: Optional[str] = Field(default=None, description="야근 상세 업무 내용")
    work_date: Optional[str] = Field(
        default=None,
        description="실제 야근한 날짜 (YYYY-MM-DD 형식으로 변환될 자연어 날짜, 예: 어제, 2023-11-24)",
    )
    work_location: Optional[str] = Field(default=None, description="야근 장소")
    overtime_ampm: Optional[str] = Field(
        default=None,
        description="퇴근 시간의 AM 또는 PM (예: 'AM', 'PM', '오전', '오후')",
    )
    overtime_hour: Optional[str] = Field(
        default=None, description="퇴근 시간의 '시' (숫자, 예: '7', '19')"
    )
    overtime_minute: Optional[str] = Field(
        default=None, description="퇴근 시간의 '분' (숫자, 예: '00', '30')"
    )
    dinner_expense_amount: Optional[int] = Field(
        default=None, description="식대 비용 (숫자만, 예: 10000)"
    )
    bank_account_for_deposit: Optional[str] = Field(
        default=None,
        description="식대 비용 입금 요청 계좌 정보 (은행명, 계좌번호, 예금주)",
    )


class TransportationExpenseSlots(BaseModel):
    """교통비 신청서 슬롯"""

    title: Optional[str] = Field(default=None, description="문서 제목")
    departure_date: Optional[str] = Field(
        default=None,
        description="출발일 또는 사용일 (YYYY-MM-DD 형식, 자연어 입력 가능)",
    )
    # arrival_date: Optional[str] = Field(default=None, description="도착일 (YYYY-MM-DD 형식, 자연어 입력 가능)") # 필요시 추가
    origin: Optional[str] = Field(default=None, description="출발지")
    destination: Optional[str] = Field(default=None, description="목적지")
    purpose: Optional[str] = Field(default=None, description="목적 또는 용무")
    transport_details: Optional[str] = Field(
        default=None,
        description="교통 내역 상세 (예: 지하철 (강남역 -> 시청역) 1,450원)",
    )
    total_amount: Optional[int] = Field(default=None, description="총 금액 (숫자)")
    notes: Optional[str] = Field(default=None, description="기타 보고 사항 또는 비고")


class DispatchBusinessTripReportSlots(BaseModel):
    """파견 및 출장 보고서 슬롯"""

    title: Optional[str] = Field(default=None, description="문서 제목")
    start_date: Optional[str] = Field(
        default=None, description="파견/출장 시작일 (YYYY-MM-DD 형식, 자연어 입력 가능)"
    )
    end_date: Optional[str] = Field(
        default=None, description="파견/출장 종료일 (YYYY-MM-DD 형식, 자연어 입력 가능)"
    )
    duration_days: Optional[str] = Field(
        default=None, description="총 파견/출장 일수 (숫자)"
    )
    origin: Optional[str] = Field(default=None, description="출발지")
    destination: Optional[str] = Field(default=None, description="파견지 또는 출장지")
    purpose: Optional[str] = Field(default=None, description="파견/출장 목적")
    report_details: Optional[str] = Field(
        default=None, description="주요 업무 내용 및 결과 (보고사항)"
    )
    notes: Optional[str] = Field(default=None, description="기타 특이사항")


# 결과를 하나로 묶는 타입은 이제 사용하지 않음. 각 체인이 해당 Pydantic 모델을 직접 반환.
# class FormExtractionResult(BaseModel):
#     form_type: str
#     slots: Dict[str, Any]


# API 응답 모델 (필요한 경우 정의)
# class FormResponse(BaseModel):
#     form_type: str
#     keywords: List[str]
#     slots: Dict[str, Any]
#     html_template: str
#     original_input: str
#     error: Optional[str] = None
#     message_to_user: Optional[str] = None
#     available_forms: Optional[List[str]] = None


class InventoryItem(BaseModel):
    item_name: Optional[str] = Field(None, description="품명")
    item_quantity: Optional[int] = Field(None, description="수량")
    item_unit_price: Optional[int] = Field(None, description="단가 (숫자)")
    item_total_price: Optional[int] = Field(
        None, description="금액 (숫자, 수량*단가 또는 직접 추출)"
    )
    item_purpose: Optional[str] = Field(None, description="용도")


class InventoryPurchaseReportSlots(BaseModel):
    """비품/소모품 구입내역서 필드"""

    title: Optional[str] = Field(
        default="비품/소모품 구입 요청", description="문서 제목"
    )
    request_department: Optional[str] = Field(None, description="요청 부서")
    requester_name: Optional[str] = Field(None, description="요청자 이름")
    request_date: Optional[str] = Field(None, description="요청일 (YYYY-MM-DD)")
    items: Optional[List[InventoryItem]] = Field(
        None, description="구입 내역 품목 리스트"
    )
    total_amount: Optional[int] = Field(
        None, description="총 합계 금액 (숫자, 모든 품목 금액의 합 또는 직접 추출)"
    )
    payment_method: Optional[str] = Field(None, description="대금지불방법")
    notes: Optional[str] = Field(None, description="특이사항")


class PurchaseItem(BaseModel):
    item_name: Optional[str] = Field(None, description="품명")
    item_spec: Optional[str] = Field(None, description="규격/사양")
    item_quantity: Optional[int] = Field(None, description="수량 (숫자)")
    item_unit_price: Optional[int] = Field(None, description="단가 (숫자)")
    item_total_price: Optional[int] = Field(
        None, description="금액 (숫자, 수량*단가 또는 직접 추출)"
    )
    item_delivery_request_date: Optional[str] = Field(
        None, description="납기요청일 (YYYY-MM-DD)"
    )
    item_purpose: Optional[str] = Field(None, description="사용목적")
    item_supplier: Optional[str] = Field(None, description="거래처")


class PurchaseApprovalFormSlots(BaseModel):
    """구매 품의서 필드"""

    title: Optional[str] = Field(default="구매 품의서", description="문서 제목")
    draft_department: Optional[str] = Field(None, description="기안 부서")
    drafter_name: Optional[str] = Field(None, description="기안자 이름")
    draft_date: Optional[str] = Field(None, description="기안일 (YYYY-MM-DD)")
    items: Optional[List[PurchaseItem]] = Field(
        None, description="품의 요청 항목 리스트"
    )
    total_purchase_amount: Optional[int] = Field(
        None, description="총 합계 금액 (숫자)"
    )
    payment_terms: Optional[str] = Field(None, description="결제 조건")
    delivery_location: Optional[str] = Field(None, description="납품 장소")
    attached_files_description: Optional[str] = Field(
        None, description="첨부 파일 설명"
    )
    special_notes: Optional[str] = Field(None, description="특기 사항 (요청 사유 등)")


class ExpenseItem(BaseModel):
    expense_date: Optional[str] = Field(None, description="일자 (YYYY-MM-DD)")
    expense_category: Optional[str] = Field(
        None, description="분류 (예: 물품구입비, 유류대, 식비)"
    )
    expense_amount: Optional[int] = Field(None, description="금액 (숫자)")
    expense_description: Optional[str] = Field(None, description="사용 내역")
    expense_notes: Optional[str] = Field(None, description="비고")


class PersonalExpenseReportSlots(BaseModel):
    """개인경비 사용내역서 필드"""

    title: Optional[str] = Field(default="개인경비 사용내역", description="문서 제목")
    draft_date: Optional[str] = Field(None, description="기안일 (YYYY-MM-DD)")
    usage_status: Optional[str] = Field(
        None, description="사용 현황 (개인현금 또는 개인카드)"
    )
    document_date: Optional[str] = Field(None, description="작성일자 (YYYY-MM-DD)")
    department: Optional[str] = Field(None, description="소속 부서")
    drafter_name: Optional[str] = Field(None, description="작성자 이름")
    total_amount_header: Optional[int] = Field(
        None, description="총 금액 (상단 표시용, 숫자)"
    )
    expense_reason: Optional[str] = Field(None, description="지출 사유")
    expense_items: Optional[List[ExpenseItem]] = Field(
        None, description="경비 사용 내역 리스트"
    )
    total_expense_amount: Optional[int] = Field(
        None, description="총 합계 금액 (하단 표시용, 숫자)"
    )


class CardUsageItem(BaseModel):
    usage_date: Optional[str] = Field(None, description="일자 (YYYY-MM-DD)")
    usage_category: Optional[str] = Field(
        None, description="분류 (예: 식비, 교통비, 접대비)"
    )
    usage_amount: Optional[int] = Field(None, description="금액 (숫자)")
    usage_description: Optional[str] = Field(None, description="사용 내역 (가맹점명)")
    usage_notes: Optional[str] = Field(None, description="비고 (내부 사용 목적 등)")


class CorporateCardStatementSlots(BaseModel):
    """법인카드 지출내역서 필드"""

    title: Optional[str] = Field(default="법인카드 지출내역", description="문서 제목")
    draft_date: Optional[str] = Field(None, description="기안일 (YYYY-MM-DD)")
    card_number: Optional[str] = Field(
        None, description="카드번호 (예: 1234-56**-****-7890)"
    )
    document_date: Optional[str] = Field(None, description="작성일자 (YYYY-MM-DD)")
    department: Optional[str] = Field(None, description="소속 부서")
    drafter_name: Optional[str] = Field(None, description="작성자 이름")
    total_amount_header: Optional[int] = Field(
        None, description="총 금액 (상단 표시용, 숫자)"
    )
    expense_reason: Optional[str] = Field(None, description="지출 사유 (간략히)")
    card_usage_items: Optional[List[CardUsageItem]] = Field(
        None, description="카드 사용 내역 리스트"
    )
    total_usage_amount: Optional[int] = Field(
        None, description="총 합계 금액 (하단 표시용, 숫자)"
    )


# 슬롯 추출 결과
class SlotExtractionResult(BaseModel):
    report_details: Optional[str] = Field(None, description="보고 사항")
    other_notes: Optional[str] = Field(None, description="기타 특이사항")
