from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class UserInput(BaseModel):
    input: str


# 1단계: 양식 분류 모델의 출력 스키마
class FormClassifierOutput(BaseModel):
    form_type: str = Field(
        description="추천된 결재 양식의 종류 (예: 연차 신청서, 회의비 지출결의서 등)"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="사용자 입력에서 추출된 RAG 검색용 주요 키워드 리스트",
    )


# 2단계: 양식별 슬롯 추출 모델의 출력 스키마들
class AnnualLeaveSlots(BaseModel):
    start_date: Optional[str] = Field(
        default=None, description="연차 시작일 (자연어 형태, 예: 다음 주 월요일)"
    )
    end_date: Optional[str] = Field(
        default=None, description="연차 종료일 (자연어 형태, 예: 다음 주 수요일)"
    )
    duration: Optional[str] = Field(default=None, description="연차 기간 (예: 3일)")
    reason: Optional[str] = Field(default=None, description="연차 사유")


class BusinessTripSlots(BaseModel):
    destination: Optional[str] = Field(default=None, description="출장지")
    start_date: Optional[str] = Field(
        default=None, description="출장 시작일 (자연어 형태)"
    )
    end_date: Optional[str] = Field(
        default=None, description="출장 종료일 (자연어 형태)"
    )
    duration: Optional[str] = Field(default=None, description="출장 기간 (예: 2박 3일)")
    transportation: Optional[str] = Field(
        default=None, description="교통편 (예: KTX, 항공)"
    )
    accommodation: Optional[str] = Field(default=None, description="숙소 정보")
    expense_details: Optional[str] = Field(default=None, description="기타 경비 내역")


class MeetingExpenseSlots(BaseModel):
    meeting_name: Optional[str] = Field(default=None, description="회의명")
    meeting_datetime: Optional[str] = Field(
        default=None, description="회의 일시 (시간 포함 자연어, 예: 오늘 오후 3시)"
    )
    amount: Optional[str] = Field(default=None, description="총 지출 금액 (예: 5만원)")
    attendees_list: Optional[str] = Field(
        default=None, description="참석자 명단 (쉼표로 구분된 문자열)"
    )
    attendees_count: Optional[str] = Field(
        default=None, description="참석자 수 (예: 3명)"
    )
    expense_details: Optional[str] = Field(
        default=None, description="전체 지출 내역 상세 설명"
    )
    venue_fee: Optional[str] = Field(
        default=None, description="장소 대관료 (해당하는 경우)"
    )
    refreshment_fee: Optional[str] = Field(
        default=None, description="다과비 (해당하는 경우)"
    )


class OtherExpenseSlots(BaseModel):
    expense_date: Optional[str] = Field(
        default=None, description="비용 발생일 (자연어 형태)"
    )
    description: Optional[str] = Field(default=None, description="비용 내용 상세 설명")
    amount: Optional[str] = Field(default=None, description="총 지출 금액")
    recipient_account: Optional[str] = Field(
        default=None, description="수취인 계좌 정보 (필요한 경우)"
    )


# 기존 FormSelectorOutput은 더 이상 사용되지 않음 (필요시 주석 처리 또는 삭제)
# class FormSelectorOutput(BaseModel):
#     form_type: str = Field(description="추천된 결재 양식의 종류 (예: 연차 신청서, 회의비 지출결의서 등)")
#     keywords: List[str] = Field(default_factory=list, description="사용자 입력에서 추출된 RAG 검색용 주요 키워드 리스트")
#     slots: Dict[str, str] = Field(default_factory=dict, description="추출된 슬롯 정보 (예: {'start_date': '내일', 'reason': '개인 사정'})")
