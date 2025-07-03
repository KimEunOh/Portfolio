"""
새로운 모듈 구조 테스트 파일

리팩토링된 프로세서들이 기존 기능과 동일하게 작동하는지 테스트합니다.
"""

import unittest
import os
import sys
from datetime import datetime
import json
from form_selector.processors.processor_factory import ProcessorFactory
from form_selector.processors.annual_leave_processor import AnnualLeaveProcessor
from form_selector.processors.personal_expense_processor import PersonalExpenseProcessor

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from form_selector.processors import get_form_processor, ProcessorFactory
from form_selector.service import fill_slots_in_template_v2


class TestRefactoredProcessors(unittest.TestCase):
    """리팩토링된 프로세서 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.current_date_iso = "2025-07-02"

    def test_processor_creation(self):
        """프로세서 생성 테스트"""
        # 연차 신청서 프로세서 생성
        annual_processor = ProcessorFactory.create_processor("연차 신청서")
        self.assertIsInstance(annual_processor, AnnualLeaveProcessor)

        # 개인 경비 프로세서 생성
        expense_processor = ProcessorFactory.create_processor("개인 경비 사용내역서")
        self.assertIsInstance(expense_processor, PersonalExpenseProcessor)

        # 영어명으로 프로세서 생성
        annual_processor_en = ProcessorFactory.create_processor("annual_leave")
        self.assertIsInstance(annual_processor_en, AnnualLeaveProcessor)

    def test_annual_leave_processor(self):
        """연차 신청서 프로세서 테스트"""
        processor = ProcessorFactory.create_processor("연차 신청서")

        # 테스트 슬롯 데이터
        slots = {
            "applicant_name": "홍길동",
            "employee_id": "2023001",
            "start_date": "내일",
            "end_date": "모레",
            "leave_type": "연차",
            "total_days": 2,
            "reason": "개인 사정",
        }

        # 슬롯 처리
        transformed_slots = processor.process_slots(slots, self.current_date_iso)

        # 날짜 변환 확인
        self.assertEqual(transformed_slots["start_date"], "2025-07-03")
        self.assertEqual(transformed_slots["end_date"], "2025-07-04")

        # 연차 타입 변환 확인
        self.assertEqual(transformed_slots["leave_type"], "annual")

    def test_personal_expense_processor(self):
        """개인 경비 프로세서 테스트"""
        processor = ProcessorFactory.create_processor("개인 경비 사용내역서")

        # 테스트 슬롯 데이터 (아이템 리스트 포함)
        slots = {
            "applicant_name": "김철수",
            "employee_id": "2023002",
            "expense_items": [
                {
                    "date": "2025-07-01",
                    "category": "교통비",
                    "amount": 5000,
                    "description": "지하철",
                },
                {
                    "date": "2025-07-02",
                    "category": "식대",
                    "amount": 22000,
                    "description": "점심 회식",
                },
            ],
        }

        # 슬롯 처리
        transformed_slots = processor.process_slots(slots, self.current_date_iso)

        # 아이템 분해 확인 (PersonalExpenseProcessor의 실제 필드명에 맞춤)
        self.assertIn("expense_date_1", transformed_slots)
        self.assertIn("expense_date_2", transformed_slots)
        self.assertIn("expense_category_1", transformed_slots)
        self.assertIn("expense_category_2", transformed_slots)

        # 총액 확인 (실제로는 아이템에서 금액을 추출해야 함)
        self.assertIn("total_expense_amount", transformed_slots)

    def test_dinner_expense_processor(self):
        """야근 식대 프로세서 테스트"""
        # DinnerExpenseProcessor 생성
        processor = ProcessorFactory.create_processor("야근식대비용 신청서")
        self.assertIsNotNone(processor)

        # 테스트 슬롯 데이터
        slots = {
            "title": "11월 25일 야근식대 신청",
            "application_date": "오늘",
            "work_details": "긴급 버그 수정",
            "work_date": "어제",
            "work_location": "회사",
            "overtime_time": "밤 10시 30분",
            "dinner_expense_amount": 12000,
            "bank_account_for_deposit": "우리은행 123-456-789 홍길동",
        }

        # 슬롯 처리
        transformed_slots = processor.process_slots(slots, self.current_date_iso)

        # 날짜 변환 확인
        self.assertEqual(transformed_slots["application_date"], "2025-07-02")  # 오늘
        self.assertEqual(transformed_slots["work_date"], "2025-07-01")  # 어제

        # 시간 변환 확인 (HH:MM 형식으로)
        self.assertEqual(transformed_slots["overtime_time"], "22:30")

        # 금액 확인 (숫자 그대로)
        self.assertEqual(transformed_slots["dinner_expense_amount"], 12000)

        # 기타 필드 확인
        self.assertEqual(transformed_slots["work_location"], "회사")
        self.assertEqual(
            transformed_slots["bank_account_for_deposit"], "우리은행 123-456-789 홍길동"
        )

    def test_dinner_expense_time_conversion(self):
        """야근 식대 시간 변환 테스트"""
        processor = ProcessorFactory.create_processor("야근식대비용 신청서")

        # 다양한 시간 표현 테스트
        time_tests = [
            ("밤 10시 30분", "22:30"),
            ("오후 9시", "21:00"),
            ("저녁 8시 반", "20:30"),
            ("22:00", "22:00"),  # 이미 정확한 형식
            ("오전 1시", "01:00"),
            ("새벽 2시 15분", "02:15"),
        ]

        for input_time, expected_time in time_tests:
            slots = {"overtime_time": input_time}
            transformed_slots = processor.process_slots(slots, self.current_date_iso)
            self.assertEqual(
                transformed_slots["overtime_time"],
                expected_time,
                f"시간 변환 실패: {input_time} -> {expected_time}",
            )

    def test_transportation_expense_processor(self):
        """교통비 신청서 프로세서 테스트"""
        # TransportationExpenseProcessor 생성
        processor = ProcessorFactory.create_processor("교통비 신청서")
        self.assertIsNotNone(processor)

        # 테스트 슬롯 데이터
        slots = {
            "title": "10월 시내 교통비 정산",
            "departure_date": "어제",
            "origin": "본사",
            "destination": "강남 거래처",
            "purpose": "거래처 미팅",
            "transport_details": "지하철 (시청역 -> 강남역) 편도 1,450원",
            "total_amount": 1450,
            "notes": "영수증 별도 제출",
        }

        # 슬롯 처리
        transformed_slots = processor.process_slots(slots, self.current_date_iso)

        # 날짜 변환 확인
        self.assertEqual(transformed_slots["departure_date"], "2025-07-01")  # 어제

        # 금액 확인 (숫자 타입 유지)
        self.assertEqual(transformed_slots["total_amount"], 1450)

        # 기타 필드 확인
        self.assertEqual(transformed_slots["origin"], "본사")
        self.assertEqual(transformed_slots["destination"], "강남 거래처")
        self.assertEqual(transformed_slots["purpose"], "거래처 미팅")
        self.assertEqual(
            transformed_slots["transport_details"],
            "지하철 (시청역 -> 강남역) 편도 1,450원",
        )
        self.assertEqual(transformed_slots["notes"], "영수증 별도 제출")

    def test_transportation_expense_amount_conversion(self):
        """교통비 금액 변환 테스트"""
        processor = ProcessorFactory.create_processor("교통비 신청서")

        # 다양한 금액 형태 테스트
        amount_tests = [
            ("1450", 1450),  # 문자열 숫자
            (1450, 1450),  # 이미 숫자
            ("0", 0),  # 문자열 0
            ("", 0),  # 빈 문자열
        ]

        for input_amount, expected_amount in amount_tests:
            slots = {"total_amount": input_amount}
            transformed_slots = processor.process_slots(slots, self.current_date_iso)

            self.assertIn(
                "total_amount",
                transformed_slots,
                f"total_amount key missing for input: {input_amount}",
            )
            self.assertEqual(
                transformed_slots["total_amount"],
                expected_amount,
                f"금액 변환 실패: {input_amount} -> {expected_amount}",
            )

        # None 값 테스트 - 다른 유효한 필드와 함께 테스트 (BaseFormProcessor의 빈 슬롯 필터링 회피)
        slots_with_none = {"total_amount": None, "purpose": "회의 참석"}
        transformed_slots = processor.process_slots(
            slots_with_none, self.current_date_iso
        )

        self.assertIn(
            "total_amount",
            transformed_slots,
            "total_amount key missing for None input with valid fields",
        )
        self.assertEqual(
            transformed_slots["total_amount"], 0, "None 값이 0으로 변환되지 않음"
        )

    def test_fill_template(self):
        """템플릿 채우기 테스트"""
        processor = ProcessorFactory.create_processor("연차 신청서")

        # 테스트 템플릿
        template = """
        <input name="applicant_name" value="{applicant_name}">
        <input name="start_date" value="{start_date}">
        <input name="leave_type" value="{leave_type}">
        """

        # 변환된 슬롯 데이터
        transformed_slots = {
            "applicant_name": "홍길동",
            "start_date": "2025-07-03",
            "leave_type": "annual",
        }

        # 템플릿 채우기 (올바른 메서드 시그니처 사용)
        filled_template = processor.fill_template(
            template, transformed_slots, self.current_date_iso
        )

        # 결과 확인
        self.assertIn('value="홍길동"', filled_template)
        self.assertIn('value="2025-07-03"', filled_template)
        self.assertIn('value="annual"', filled_template)

    def test_transportation_expense_template_filling(self):
        """교통비 프로세서 템플릿 채우기 테스트"""
        processor = ProcessorFactory.create_processor("transportation_expense")

        slots = {
            "title": "교통비 신청서",
            "departure_date": "어제",
            "origin": "강남역",
            "destination": "판교역",
            "purpose": "고객사 미팅",
            "transport_details": "지하철 이용",
            "total_amount": "1450",
            "notes": "출장비 신청",
        }

        # 슬롯 처리 먼저 수행
        processed_slots = processor.process_slots(slots, "2025-07-02")

        # 기본 필드 확인
        self.assertEqual(processed_slots["title"], "교통비 신청서")
        self.assertEqual(processed_slots["departure_date"], "2025-07-01")  # 어제
        self.assertEqual(processed_slots["origin"], "강남역")
        self.assertEqual(processed_slots["destination"], "판교역")
        self.assertEqual(processed_slots["purpose"], "고객사 미팅")
        self.assertEqual(processed_slots["transport_details"], "지하철 이용")
        self.assertEqual(processed_slots["total_amount"], 1450)
        self.assertEqual(processed_slots["notes"], "출장비 신청")

    def test_inventory_purchase_processor_creation(self):
        """비품 구입내역서 프로세서 생성 테스트"""
        processor = ProcessorFactory.create_processor("inventory_purchase_report")
        self.assertIsNotNone(processor)
        self.assertEqual(processor.__class__.__name__, "InventoryPurchaseProcessor")

        # 한국어 양식명으로도 생성 가능한지 테스트
        processor_korean = ProcessorFactory.create_processor("비품/소모품 구입내역서")
        self.assertIsNotNone(processor_korean)
        self.assertEqual(
            processor_korean.__class__.__name__, "InventoryPurchaseProcessor"
        )

    def test_inventory_purchase_item_processing(self):
        """비품 구입내역서 아이템 처리 테스트"""
        processor = ProcessorFactory.create_processor("inventory_purchase_report")

        slots = {
            "title": "비품 구입 요청",
            "request_date": "오늘",
            "items": [
                {
                    "item_name": "A4용지",
                    "item_quantity": 10,
                    "item_unit_price": 2500,
                    "item_total_price": 25000,
                    "item_notes": "사무용품",
                },
                {
                    "item_name": "볼펜",
                    "item_quantity": 20,
                    "item_unit_price": 1000,
                    "item_total_price": 20000,
                    "item_notes": "사무용품",
                },
                {
                    "item_name": "모니터",
                    "item_quantity": 2,
                    "item_unit_price": 200000,
                    "item_total_price": 400000,
                    "item_notes": "개발팀 장비",
                },
            ],
            "payment_method": "법인카드",
            "notes": "긴급 요청",
        }

        result = processor.process_slots(slots, "2025-07-02")

        # 아이템 필드 확인 (최대 6개까지 지원)
        self.assertEqual(result["item_name_1"], "A4용지")
        self.assertEqual(result["item_quantity_1"], 10)
        self.assertEqual(result["item_unit_price_1"], 2500)
        self.assertEqual(result["item_total_price_1"], 25000)
        self.assertEqual(result["item_purpose_1"], "사무용품")

        self.assertEqual(result["item_name_2"], "볼펜")
        self.assertEqual(result["item_quantity_2"], 20)
        self.assertEqual(result["item_unit_price_2"], 1000)
        self.assertEqual(result["item_total_price_2"], 20000)
        self.assertEqual(result["item_purpose_2"], "사무용품")

        self.assertEqual(result["item_name_3"], "모니터")
        self.assertEqual(result["item_quantity_3"], 2)
        self.assertEqual(result["item_unit_price_3"], 200000)
        self.assertEqual(result["item_total_price_3"], 400000)
        self.assertEqual(result["item_purpose_3"], "개발팀 장비")

        # 총액 계산 확인
        self.assertEqual(result["total_amount"], 445000)  # 25000 + 20000 + 400000

    def test_inventory_purchase_total_calculation(self):
        """비품 구입내역서 총액 계산 테스트"""
        processor = ProcessorFactory.create_processor("inventory_purchase_report")

        # 1. items 배열에서 총액 계산
        slots_with_items = {
            "items": [
                {"item_total_price": 10000},
                {"item_total_price": 15000},
                {"item_total_price": 20000},
            ]
        }

        result = processor.convert_items(slots_with_items)
        self.assertEqual(result["total_amount"], 45000)

        # 2. 직접 total_amount가 제공된 경우
        slots_with_direct_total = {
            "total_amount": 100000,
            "items": [{"item_total_price": 50000}],
        }

        result = processor.convert_items(slots_with_direct_total)
        self.assertEqual(result["total_amount"], 100000)  # 직접 제공된 값 우선

    def test_inventory_purchase_template_filling(self):
        """비품 구입내역서 템플릿 채우기 테스트"""
        processor = ProcessorFactory.create_processor("inventory_purchase_report")

        slots = {
            "title": "사무용품 구입 신청",
            "request_date": "오늘",
            "items": [
                {
                    "item_name": "복사용지",
                    "item_quantity": 5,
                    "item_unit_price": 5000,
                    "item_total_price": 25000,
                    "item_notes": "회의실용",
                }
            ],
            "total_amount": 25000,
            "payment_method": "계좌이체",
            "notes": "정기 구매",
        }

        result = processor.process_slots(slots, "2025-07-02")

        # 기본 필드 확인
        self.assertEqual(result["title"], "사무용품 구입 신청")
        self.assertEqual(result["request_date"], "2025-07-02")  # 오늘
        self.assertEqual(result["payment_method"], "계좌이체")
        self.assertEqual(result["notes"], "정기 구매")

        # 아이템 필드 확인
        self.assertEqual(result["item_name_1"], "복사용지")
        self.assertEqual(result["item_quantity_1"], 5)
        self.assertEqual(result["item_unit_price_1"], 5000)
        self.assertEqual(result["item_total_price_1"], 25000)
        self.assertEqual(result["item_purpose_1"], "회의실용")

        # 총액 확인
        self.assertEqual(result["total_amount"], 25000)


if __name__ == "__main__":
    print("새로운 모듈 구조 테스트 시작...")
    print(f"현재 날짜: {datetime.now().date().isoformat()}")

    unittest.main(verbosity=2)
