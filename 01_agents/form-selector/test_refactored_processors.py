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


if __name__ == "__main__":
    print("새로운 모듈 구조 테스트 시작...")
    print(f"현재 날짜: {datetime.now().date().isoformat()}")

    unittest.main(verbosity=2)
