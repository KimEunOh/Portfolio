import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# 테스트 대상 함수 임포트
from form_selector.service import classify_and_extract_slots_for_template
from form_selector.schema import (
    UserInput,
    FormClassificationOutput,
    AnnualLeaveSlots,
    DinnerExpenseSlots,
    TransportationExpenseSlots,
    DispatchBusinessTripReportSlots,
    InventoryPurchaseReportSlots,
    PurchaseApprovalFormSlots,
    PersonalExpenseReportSlots,
    CorporateCardStatementSlots,
    ApproverInfoResponse,
    ApproverInfoData,
)

# 테스트의 일관성을 위한 기준 날짜 (2025년 7월 24일 목요일)
TODAY_ISO = "2025-07-24"

# --- 8가지 양식에 대한 테스트 케이스 정의 ---
TEST_CASES = [
    # 1. 연차 신청서 (LLM 판단) - 미래
    {
        "description": "Annual Leave (Future)",
        "form_type": "연차 신청서",
        "user_input": "다음 주 월요일부터 연차 쓸게요.",
        "mock_slots": AnnualLeaveSlots(
            start_date="다음 주 월요일", time_context="FUTURE"
        ),
        "expected_dates": {"start_date": "2025-07-28"},
    },
    # 2. 연차 신청서 (LLM 판단) - 과거
    {
        "description": "Annual Leave (Past)",
        "form_type": "연차 신청서",
        "user_input": "지난 주 월요일에 쓴 연차 사후 제출합니다.",
        "mock_slots": AnnualLeaveSlots(
            start_date="지난 주 월요일", time_context="PAST"
        ),
        "expected_dates": {"start_date": "2025-07-14"},
    },
    # 3. 야근식대비용 신청서 (과거 고정)
    {
        "description": "Dinner Expense (Past Fixed)",
        "form_type": "야근식대비용 신청서",
        "user_input": "어제 야근 식대입니다.",
        "mock_slots": DinnerExpenseSlots(work_date="어제"),
        "expected_dates": {"work_date": "2025-07-23"},
    },
    # 4. 교통비 신청서 (과거 고정)
    {
        "description": "Transportation Expense (Past Fixed)",
        "form_type": "교통비 신청서",
        "user_input": "이번 주 화요일에 쓴 택시비요.",
        "mock_slots": TransportationExpenseSlots(departure_date="이번 주 화요일"),
        "expected_dates": {"departure_date": "2025-07-22"},
    },
    # 5. 파견 및 출장 보고서 (LLM 판단) - 미래
    {
        "description": "Dispatch Report (Future)",
        "form_type": "파견 및 출장 보고서",
        "user_input": "다음 달 출장 계획 보고합니다. 8월 4일부터 8월 5일까지입니다.",
        "mock_slots": DispatchBusinessTripReportSlots(
            start_date="8월 4일", end_date="8월 5일", time_context="FUTURE"
        ),
        "expected_dates": {"start_date": "2025-08-04", "end_date": "2025-08-05"},
    },
    # 6. 파견 및 출장 보고서 (LLM 판단) - 과거
    {
        "description": "Dispatch Report (Past)",
        "form_type": "파견 및 출장 보고서",
        "user_input": "6월 23일부터 24일까지 다녀온 출장 결과입니다.",
        "mock_slots": DispatchBusinessTripReportSlots(
            start_date="6월 23일", end_date="6월 24일", time_context="PAST"
        ),
        "expected_dates": {"start_date": "2025-06-23", "end_date": "2025-06-24"},
    },
    # 7. 비품/소모품 구입내역서 (미래 고정)
    {
        "description": "Inventory Purchase (Future Fixed)",
        "form_type": "비품/소모품 구입내역서",
        "user_input": "내일 사무용품 구매 요청합니다.",
        "mock_slots": InventoryPurchaseReportSlots(request_date="내일"),
        "expected_dates": {"request_date": "2025-07-25"},
    },
    # 8. 구매 품의서 (미래 고정)
    {
        "description": "Purchase Approval (Future Fixed)",
        "form_type": "구매 품의서",
        "user_input": "다음 달 1일에 납품받을 물건 구매 품의 올립니다.",
        "mock_slots": PurchaseApprovalFormSlots(
            items=[{"item_delivery_request_date": "다음 달 1일", "item_total_price": 0}]
        ),
        "expected_dates": {"items": [{"item_delivery_request_date": "2025-08-01"}]},
    },
    # 9. 개인 경비 사용 내역서 (과거 고정)
    {
        "description": "Personal Expense (Past Fixed)",
        "form_type": "개인 경비 사용 내역서",
        "user_input": "이틀 전에 쓴 개인 경비입니다.",
        "mock_slots": PersonalExpenseReportSlots(
            expense_items=[{"expense_date": "이틀 전"}]
        ),
        "expected_dates": {"statement_date": "2025-07-22"},
    },
    # 10. 법인카드 지출내역서 (과거 고정)
    {
        "description": "Corporate Card (Past Fixed)",
        "form_type": "법인카드 지출내역서",
        "user_input": "이번 주 월요일에 사용한 법인카드 내역입니다.",
        "mock_slots": CorporateCardStatementSlots(
            card_usage_items=[{"usage_date": "이번 주 월요일", "usage_amount": 0}]
        ),
        "expected_dates": {"statement_date": "2025-07-21"},
    },
]


@pytest.mark.parametrize(
    "test_case", TEST_CASES, ids=[tc["description"] for tc in TEST_CASES]
)
@patch("form_selector.service.get_form_classifier_chain")
@patch("form_selector.llm.SLOT_EXTRACTOR_CHAINS")
@patch("form_selector.service.retrieve_template")
@patch("form_selector.service.datetime")
@patch("form_selector.service.get_approval_info")
def test_date_conversion_for_all_forms(
    mock_get_approval_info,
    mock_datetime,
    mock_retrieve_template,
    mock_slot_chains,
    mock_classifier_chain,
    test_case,
):
    # --- 1. 모의(Mock) 객체 설정 ---

    # datetime.now()가 항상 고정된 날짜를 반환하도록 설정
    mock_datetime.now.return_value = datetime.strptime(TODAY_ISO, "%Y-%m-%d")

    # 양식 분류기 모의 설정
    mock_classifier = MagicMock()
    mock_classifier.invoke.return_value = FormClassificationOutput(
        form_type=test_case["form_type"]
    )
    mock_classifier_chain.return_value = mock_classifier

    # 슬롯 추출기 모의 설정
    mock_slot_extractor = MagicMock()
    mock_slot_extractor.invoke.return_value = test_case["mock_slots"]
    mock_slot_chains.__getitem__.return_value = mock_slot_extractor

    # 템플릿 검색 모의 설정
    mock_retrieve_template.return_value = "<div>{start_date} {end_date} {work_date} {departure_date} {request_date} {draft_date}</div>"

    # 결재자 정보 조회 모의 설정
    mock_get_approval_info.return_value = ApproverInfoResponse(
        code=1,
        message="Success",
        data=ApproverInfoData(drafterName="", drafterDepartment="", approvers=[]),
    )

    # --- 2. 테스트 실행 ---
    user_input = UserInput(input=test_case["user_input"])
    result = classify_and_extract_slots_for_template(user_input)

    # --- 3. 결과 검증 ---
    assert "error" not in result, f"Test failed with error: {result.get('error')}"

    processed_slots = result.get("slots", {})

    # 예상되는 날짜 슬롯 값과 실제 처리된 값을 비교
    for key, expected_value in test_case["expected_dates"].items():
        assert (
            key in processed_slots
        ), f"Expected key '{key}' not found in processed slots."

        actual_value = processed_slots[key]

        if isinstance(expected_value, list):  # 개인경비, 법인카드 등 항목 리스트 검증
            assert isinstance(actual_value, list)
            assert len(actual_value) == len(expected_value)
            # 현재 테스트는 항목이 하나인 경우만 다룸
            date_key = list(expected_value[0].keys())[0]
            assert actual_value[0][date_key] == expected_value[0][date_key]
        else:  # 일반 날짜 필드 검증
            assert (
                actual_value == expected_value
            ), f"Mismatch for '{key}': expected '{expected_value}', got '{actual_value}'"

    print(f"\n✅ Passed: {test_case['description']}")
    print(f"  Input: '{test_case['user_input']}'")
    print(f"  Result: {test_case['expected_dates']}")
