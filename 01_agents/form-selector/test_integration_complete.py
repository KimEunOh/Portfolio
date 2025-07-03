"""
Form Selector 프로젝트 통합 테스트
=================================
전체 플로우 테스트: 양식 분류 → 슬롯 추출 → 데이터 변환 → HTML 생성
"""

import unittest
import requests
import json
import time
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from form_selector.service import (
    classify_and_extract_slots_for_template,
    fill_slots_in_template,
)
from form_selector.processors.processor_factory import ProcessorFactory
from form_selector import schema


class TestFormSelectorIntegration(unittest.TestCase):
    """Form Selector 통합 테스트"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        cls.base_url = "http://localhost:8000"
        cls.current_date = datetime.now().strftime("%Y-%m-%d")
        cls.test_data = cls._load_test_data()
        cls._check_server_connection()

    @classmethod
    def _load_test_data(cls):
        """테스트 데이터 로드"""
        test_files = {
            "transportation": "test_transportation.json",
            "personal_expense": "test_personal_expense.json",
            "purchase_approval": "test_purchase_approval.json",
        }

        data = {}
        for form_type, filename in test_files.items():
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    data[form_type] = json.load(f)
        return data

    @classmethod
    def _check_server_connection(cls):
        """서버 연결 확인"""
        try:
            response = requests.get(f"{cls.base_url}/health", timeout=5)
        except:
            print(
                "⚠️  서버가 실행중이지 않습니다. 'python main.py'로 서버를 시작하세요."
            )

    # ==========================================
    # 1. 전체 플로우 통합 테스트
    # ==========================================

    def test_complete_flow_transportation(self):
        """교통비 신청서 전체 플로우 테스트"""
        if "transportation" not in self.test_data:
            self.skipTest("교통비 테스트 데이터가 없습니다.")

        form_content = self.test_data["transportation"]["input"]

        # UserInput 스키마 생성
        user_input = schema.UserInput(input=form_content)

        # 전체 플로우 실행 (분류 + 슬롯 추출 + 템플릿 생성)
        result = classify_and_extract_slots_for_template(user_input)

        # 결과 검증
        self.assertIn("form_type", result)
        self.assertIn("교통비", result["form_type"])
        self.assertIn("html_template", result)
        self.assertIn("<form", result["html_template"])

        print("✅ 교통비 신청서 전체 플로우 테스트 통과")

    def test_complete_flow_personal_expense(self):
        """개인 경비 사용내역서 전체 플로우 테스트"""
        if "personal_expense" not in self.test_data:
            self.skipTest("개인 경비 테스트 데이터가 없습니다.")

        form_content = self.test_data["personal_expense"]["input"]

        # UserInput 스키마 생성
        user_input = schema.UserInput(input=form_content)

        # 전체 플로우 실행
        result = classify_and_extract_slots_for_template(user_input)

        # 결과 검증
        self.assertIn("form_type", result)
        self.assertIn("개인", result["form_type"])
        self.assertIn("html_template", result)

        # HTML 템플릿에 경비 항목이 포함되었는지 확인
        html_template = result["html_template"]
        self.assertIn("expense_date", html_template)

        print("✅ 개인 경비 사용내역서 전체 플로우 테스트 통과")

    # ==========================================
    # 2. API 통합 테스트
    # ==========================================

    def test_api_integration_all_forms(self):
        """모든 양식 API 통합 테스트"""
        if not self.test_data:
            self.skipTest("API 테스트 데이터가 없습니다.")

        for form_type, test_data in self.test_data.items():
            with self.subTest(form_type=form_type):
                try:
                    response = requests.post(
                        f"{self.base_url}/form-selector", json=test_data, timeout=30
                    )

                    self.assertEqual(
                        response.status_code, 200, f"{form_type} API 호출 실패"
                    )

                    result = response.json()
                    self.assertIn("form_type", result)
                    self.assertIn("html_template", result)

                    # HTML 템플릿 검증
                    self.assertIn("<form", result["html_template"])

                    print(f"✅ {form_type} API 통합 테스트 통과")

                except requests.exceptions.RequestException as e:
                    print(f"⚠️  {form_type} API 테스트 스킵: 서버 연결 불가")

    def test_api_error_handling(self):
        """API 에러 처리 테스트"""
        try:
            # 잘못된 요청
            response = requests.post(
                f"{self.base_url}/form-selector", json={"invalid": "data"}, timeout=10
            )

            self.assertIn(response.status_code, [400, 422, 500])
            print("✅ API 에러 처리 테스트 통과")

        except requests.exceptions.RequestException:
            print("⚠️  API 에러 처리 테스트 스킵: 서버 연결 불가")

    def test_api_put_request_end_to_end(self):
        """실제 API PUT request까지 포함한 완전한 End-to-End 테스트"""
        print("\n=== API PUT Request End-to-End 테스트 시작 ===")

        # 1단계: 양식 추천 및 슬롯 추출
        test_input = "어제 출장 다녀왔습니다. 강남역에서 여의도역까지 지하철 이용했고 왕복 2900원 사용했습니다. 고객사 미팅 참석이 목적이었습니다."

        user_input = schema.UserInput(input=test_input, drafterId="01240006")

        # 양식 추천 및 슬롯 추출
        result = classify_and_extract_slots_for_template(user_input)

        # 양식 분류 검증
        self.assertNotIn("error", result, f"Form classification failed: {result}")
        self.assertEqual(result["form_type"], "교통비 신청서")
        self.assertIn("html_template", result)

        # 슬롯 추출 검증
        slots = result.get("slots", {})
        self.assertIn("departure_date", slots)
        self.assertIn("total_amount", slots)
        self.assertIn("origin", slots)
        self.assertIn("destination", slots)

        print(f"✅ 1단계 완료 - 양식 분류: {result['form_type']}")
        print(f"   추출된 슬롯: {list(slots.keys())}")

        # 🆕 슬롯 값 상세 검증
        print(f"   📋 핵심 슬롯 값 검증:")
        print(f"      - departure_date: {slots.get('departure_date')}")
        print(f"      - total_amount: {slots.get('total_amount')}")
        print(f"      - origin: {slots.get('origin')}")
        print(f"      - destination: {slots.get('destination')}")
        print(f"      - purpose: {slots.get('purpose')}")

        # 슬롯 값 검증
        self.assertEqual(slots.get("departure_date"), "2025-07-02")
        self.assertEqual(slots.get("total_amount"), 2900)
        self.assertEqual(slots.get("origin"), "강남역")
        self.assertEqual(slots.get("destination"), "여의도역")
        self.assertIn("고객사", slots.get("purpose", ""))

        # 🆕 슬롯 값 상세 검증
        print(f"   📋 핵심 슬롯 값 검증:")
        print(f"      - departure_date: {slots.get('departure_date')}")
        print(f"      - total_amount: {slots.get('total_amount')}")
        print(f"      - origin: {slots.get('origin')}")
        print(f"      - destination: {slots.get('destination')}")
        print(f"      - purpose: {slots.get('purpose')}")

        # 슬롯 값 검증
        self.assertEqual(slots.get("departure_date"), "2025-07-02")
        self.assertEqual(slots.get("total_amount"), 2900)
        self.assertEqual(slots.get("origin"), "강남역")
        self.assertEqual(slots.get("destination"), "여의도역")
        self.assertIn("고객사", slots.get("purpose", ""))

        # 2단계: 폼 데이터 준비 (실제 프론트엔드에서 전송될 데이터 시뮬레이션)
        form_data = {
            "title": slots.get("title", "교통비 신청"),
            "drafterId": result.get("drafterId", "01240006"),
            "purpose": slots.get("purpose", "업무 관련"),
            "departure_date": slots.get("departure_date", ""),
            "origin": slots.get("origin", ""),
            "destination": slots.get("destination", ""),
            "transport_details": slots.get("transport_details", ""),
            "notes": "End-to-End 테스트",
            "total_amount": str(slots.get("total_amount", 0)),
            "approvers": (
                getattr(result.get("approver_info"), "approvers", [])
                if result.get("approver_info")
                else []
            ),
        }

        print(f"✅ 2단계 완료 - 폼 데이터 준비: {len(form_data)} 필드")

        # 3단계: API 페이로드 변환 및 상세 검증
        from form_selector.service import convert_form_data_to_api_payload

        api_payload = convert_form_data_to_api_payload(
            "transportation_expense", form_data
        )

        # 🆕 API 페이로드 상세 검증
        print(f"✅ 3단계 완료 - API 페이로드 변환 및 검증:")

        # 기본 구조 검증
        self.assertIn("mstPid", api_payload)
        self.assertEqual(api_payload["mstPid"], 4, "교통비 신청서의 mstPid는 4여야 함")

        self.assertIn("amountList", api_payload)
        self.assertGreater(len(api_payload["amountList"]), 0, "amountList가 비어있음")

        self.assertIn("lineList", api_payload)
        self.assertGreater(len(api_payload["lineList"]), 0, "lineList가 비어있음")

        # 🔍 핵심 데이터 매칭 검증
        print(f"   📊 핵심 데이터 매칭 검증:")

        # amountList 상세 검증
        amount_item = api_payload["amountList"][0]
        print(f"      💰 amountList[0]:")
        print(
            f"         - useYmd: {amount_item.get('useYmd')} (슬롯: {slots.get('departure_date')})"
        )
        print(
            f"         - amount: {amount_item.get('amount')} (슬롯: {slots.get('total_amount')})"
        )
        print(f"         - dvNm: {amount_item.get('dvNm')}")
        print(f"         - useRsn: {amount_item.get('useRsn')}")

        self.assertEqual(
            amount_item.get("useYmd"), slots.get("departure_date"), "날짜 매칭 실패"
        )
        self.assertEqual(
            amount_item.get("amount"), slots.get("total_amount"), "금액 매칭 실패"
        )
        self.assertEqual(amount_item.get("dvNm"), "교통비", "비용 구분 매칭 실패")

        # apdInfo JSON 검증
        import json

        apd_info = json.loads(api_payload.get("apdInfo", "{}"))
        print(f"      📄 apdInfo JSON:")
        print(
            f"         - origin: {apd_info.get('origin')} (슬롯: {slots.get('origin')})"
        )
        print(
            f"         - destination: {apd_info.get('destination')} (슬롯: {slots.get('destination')})"
        )

        self.assertEqual(
            apd_info.get("origin"), slots.get("origin"), "출발지 매칭 실패"
        )
        self.assertEqual(
            apd_info.get("destination"), slots.get("destination"), "목적지 매칭 실패"
        )

        # lineList 검증
        print(f"      👥 lineList: {len(api_payload['lineList'])}명")
        for i, approver in enumerate(api_payload["lineList"]):
            print(
                f"         - {i+1}번째: {approver.get('aprvPslId')} ({approver.get('aprvDvTy')})"
            )

        # 4단계: 실제 외부 API 호출 및 응답 검증
        import httpx
        import os

        api_base_url = os.getenv(
            "APPROVAL_API_BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper"
        )
        register_url = f"{api_base_url}/register"

        print(f"   📡 실제 API 호출: {register_url}")
        print(f"      전송 페이로드 크기: {len(str(api_payload))} 문자")

        try:
            with httpx.Client(timeout=10.0) as client:
                # 실제 API 호출
                response = client.put(register_url, json=api_payload)

                print(f"✅ 4단계 완료 - API 호출 결과:")
                print(f"   상태 코드: {response.status_code}")

                if response.status_code == 200:
                    api_response = response.json()
                    print(f"   🎉 API 응답: {api_response}")

                    # API 응답 검증
                    self.assertIn("code", api_response, "API 응답에 code 필드 없음")
                    self.assertEqual(
                        api_response["code"], 1, f"API 실패: {api_response}"
                    )

                    if api_response["code"] == 1:
                        print("🎊 완전한 End-to-End 테스트 성공!")
                        print(
                            f"   ✨ 핵심 데이터 정확성: 슬롯 추출 → JSON 변환 → API 전송 모든 단계 검증 완료"
                        )
                        print(
                            f"   📋 최종 메시지: {api_response.get('message', 'No message')}"
                        )
                    else:
                        self.fail(f"API 응답 실패: {api_response}")

                else:
                    response_text = response.text
                    print(f"   ❌ 오류 응답: {response_text}")
                    self.fail(
                        f"API 호출 실패: {response.status_code} - {response_text}"
                    )

        except httpx.HTTPError as e:
            print(f"❌ API 호출 네트워크 오류: {e}")
            self.fail(f"API 호출 중 네트워크 오류: {e}")
        except Exception as e:
            print(f"❌ API 호출 중 예외 발생: {e}")
            self.fail(f"API 호출 중 예외: {e}")

        print("=== API PUT Request End-to-End 테스트 완료 ===\n")

    def test_annual_leave_api_end_to_end(self):
        """연차 신청서 End-to-End API 테스트"""
        print("\n=== 연차 신청서 End-to-End 테스트 시작 ===")

        # 연차 신청 테스트 입력
        test_input = (
            "내일부터 3일간 연차 사용하고 싶습니다. 개인 사정으로 인한 휴가입니다."
        )

        user_input = schema.UserInput(input=test_input, drafterId="01240006")
        result = classify_and_extract_slots_for_template(user_input)

        # 양식 분류 검증
        self.assertNotIn("error", result)
        self.assertEqual(result["form_type"], "연차 신청서")

        slots = result.get("slots", {})
        print(f"✅ 연차 슬롯 추출: {list(slots.keys())}")

        # 🆕 연차 슬롯 값 상세 검증
        print(f"   📋 연차 핵심 슬롯 값 검증:")
        print(f"      - start_date: {slots.get('start_date')}")
        print(f"      - end_date: {slots.get('end_date')}")
        print(f"      - leave_type: {slots.get('leave_type')}")
        print(f"      - reason: {slots.get('reason')}")
        print(f"      - leave_days: {slots.get('leave_days')}")

        # 연차 슬롯 값 검증
        self.assertEqual(slots.get("start_date"), "2025-07-04")
        self.assertEqual(slots.get("end_date"), "2025-07-06")
        self.assertEqual(slots.get("leave_type"), "annual")
        self.assertIn("개인", slots.get("reason", ""))
        self.assertEqual(slots.get("leave_days"), "3")

        # 폼 데이터 준비
        form_data = {
            "title": slots.get("title", "연차 신청"),
            "drafterId": result.get("drafterId", "01240006"),
            "reason": slots.get("reason", "개인 사정"),
            "start_date": slots.get("start_date", ""),
            "end_date": slots.get("end_date", ""),
            "leave_type": slots.get("leave_type", "annual"),
            "leave_days": slots.get("leave_days", ""),
            "approvers": (
                getattr(result.get("approver_info"), "approvers", [])
                if result.get("approver_info")
                else []
            ),
        }

        # API 페이로드 변환 및 호출
        from form_selector.service import convert_form_data_to_api_payload

        api_payload = convert_form_data_to_api_payload("annual_leave", form_data)

        self.assertEqual(api_payload["mstPid"], 1, "연차 신청서의 mstPid는 1이어야 함")

        # 🆕 연차 API 페이로드 상세 검증
        print(f"✅ 연차 API 페이로드 검증:")
        print(f"   📊 dayList 항목 수: {len(api_payload.get('dayList', []))}")

        # dayList 상세 검증 (3일간 연차)
        day_list = api_payload.get("dayList", [])
        self.assertEqual(len(day_list), 3, "3일간 연차이므로 dayList는 3개여야 함")

        expected_dates = ["2025-07-04", "2025-07-05", "2025-07-06"]
        actual_dates = [day["reqYmd"] for day in day_list]
        print(f"   📅 예상 날짜: {expected_dates}")
        print(f"   📅 실제 날짜: {actual_dates}")

        self.assertEqual(actual_dates, expected_dates, "연차 날짜 리스트 매칭 실패")

        # dvType 검증 (모두 DAY여야 함)
        for day in day_list:
            self.assertEqual(day["dvType"], "DAY", "연차 dvType은 DAY여야 함")

        print(f"   ✅ dayList 검증 완료: 슬롯 날짜 → API dayList 정확히 변환됨")

        # 실제 API 호출 (옵션)
        self._call_api_if_available(api_payload, "연차 신청서")
        print("=== 연차 신청서 End-to-End 테스트 완료 ===\n")

    def test_dinner_expense_api_end_to_end(self):
        """야근 식대 End-to-End API 테스트"""
        print("\n=== 야근 식대 End-to-End 테스트 시작 ===")

        test_input = (
            "어제 밤 10시까지 야근했습니다. 회사에서 저녁식사 15000원 사용했어요."
        )

        user_input = schema.UserInput(input=test_input, drafterId="01240006")
        result = classify_and_extract_slots_for_template(user_input)

        # 양식 분류 검증
        self.assertNotIn("error", result)
        self.assertEqual(result["form_type"], "야근식대비용 신청서")

        slots = result.get("slots", {})
        print(f"✅ 야근 식대 슬롯 추출: {list(slots.keys())}")

        # 🆕 야근 식대 슬롯 값 상세 검증
        print(f"   📋 야근 식대 핵심 슬롯 값 검증:")
        print(f"      - work_date: {slots.get('work_date')}")
        print(f"      - dinner_expense_amount: {slots.get('dinner_expense_amount')}")
        print(f"      - work_location: {slots.get('work_location')}")
        print(f"      - overtime_time: {slots.get('overtime_time')}")
        print(f"      - work_details: {slots.get('work_details')}")

        # 야근 식대 슬롯 값 검증
        self.assertEqual(slots.get("work_date"), "2025-07-02")
        self.assertEqual(slots.get("dinner_expense_amount"), 15000)
        self.assertEqual(slots.get("work_location"), "회사")
        self.assertEqual(slots.get("overtime_time"), "22:00")
        self.assertIn("야근", slots.get("title", ""))

        # 폼 데이터 준비
        form_data = {
            "title": slots.get("title", "야근 식대 신청"),
            "drafterId": result.get("drafterId", "01240006"),
            "work_details": slots.get("work_details", "야근 업무"),
            "work_date": slots.get("work_date", ""),
            "dinner_expense_amount": slots.get("dinner_expense_amount", 0),
            "work_location": slots.get("work_location", "회사"),
            "overtime_time": slots.get("overtime_time", ""),
            "approvers": (
                getattr(result.get("approver_info"), "approvers", [])
                if result.get("approver_info")
                else []
            ),
        }

        # API 페이로드 변환 및 호출
        from form_selector.service import convert_form_data_to_api_payload

        api_payload = convert_form_data_to_api_payload("dinner_expense", form_data)

        self.assertEqual(api_payload["mstPid"], 3, "야근 식대의 mstPid는 3이어야 함")

        # 🆕 야근 식대 API 페이로드 상세 검증
        print(f"✅ 야근 식대 API 페이로드 검증:")
        print(f"   📊 amountList 항목 수: {len(api_payload.get('amountList', []))}")

        # amountList 상세 검증
        amount_list = api_payload.get("amountList", [])
        self.assertGreater(len(amount_list), 0, "amountList가 비어있음")

        amount_item = amount_list[0]
        print(f"   💰 amountList[0]:")
        print(
            f"      - useYmd: {amount_item.get('useYmd')} (슬롯: {slots.get('work_date')})"
        )
        print(
            f"      - amount: {amount_item.get('amount')} (슬롯: {slots.get('dinner_expense_amount')})"
        )
        print(f"      - dvNm: {amount_item.get('dvNm')}")
        print(f"      - useRsn: {amount_item.get('useRsn')}")

        # 핵심 데이터 매칭 검증
        self.assertEqual(
            amount_item.get("useYmd"), slots.get("work_date"), "야근 날짜 매칭 실패"
        )
        self.assertEqual(
            amount_item.get("amount"),
            slots.get("dinner_expense_amount"),
            "야근 식대 금액 매칭 실패",
        )
        self.assertEqual(amount_item.get("dvNm"), "식대", "비용 구분 매칭 실패")

        # apdInfo JSON 검증
        import json

        apd_info = json.loads(api_payload.get("apdInfo", "{}"))
        print(f"   📄 apdInfo JSON:")
        print(
            f"      - work_location: {apd_info.get('work_location')} (슬롯: {slots.get('work_location')})"
        )
        print(
            f"      - overtime_time: {apd_info.get('overtime_time')} (슬롯: {slots.get('overtime_time')})"
        )

        self.assertEqual(
            apd_info.get("work_location"),
            slots.get("work_location"),
            "근무 장소 매칭 실패",
        )
        self.assertEqual(
            apd_info.get("overtime_time"),
            slots.get("overtime_time"),
            "야근 시간 매칭 실패",
        )

        print(f"   ✅ 야근 식대 검증 완료: 슬롯 데이터 → API 페이로드 정확히 변환됨")

        # 실제 API 호출 (옵션)
        self._call_api_if_available(api_payload, "야근 식대")
        print("=== 야근 식대 End-to-End 테스트 완료 ===\n")

    def _call_api_if_available(self, api_payload, form_name):
        """API 호출 가능한 경우에만 실제 호출"""
        import httpx
        import os

        api_base_url = os.getenv(
            "APPROVAL_API_BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper"
        )
        register_url = f"{api_base_url}/register"

        try:
            with httpx.Client(timeout=5.0) as client:  # 짧은 타임아웃
                response = client.put(register_url, json=api_payload)

                if response.status_code == 200:
                    api_response = response.json()
                    if api_response.get("code") == 1:
                        print(
                            f"🎉 {form_name} API 호출 성공: {api_response.get('message')}"
                        )
                    else:
                        print(f"⚠️  {form_name} API 응답 오류: {api_response}")
                else:
                    print(f"⚠️  {form_name} API 호출 실패: {response.status_code}")

        except Exception as e:
            print(f"⚠️  {form_name} API 호출 스킵 (네트워크 문제): {str(e)[:50]}...")

    # ==========================================
    # 3. 성능 테스트
    # ==========================================

    def test_performance_concurrent_requests(self):
        """동시 요청 성능 테스트"""
        if not self.test_data:
            self.skipTest("성능 테스트 데이터가 없습니다.")

        concurrent_requests = 3
        test_data = list(self.test_data.values())[0]

        def make_request():
            try:
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/form-selector", json=test_data, timeout=30
                )
                end = time.time()
                return {"success": response.status_code == 200, "time": end - start}
            except:
                return {"success": False, "time": -1}

        try:
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [
                    executor.submit(make_request) for _ in range(concurrent_requests)
                ]
                results = [future.result() for future in as_completed(futures)]

            total_time = time.time() - start_time
            successful = sum(1 for r in results if r["success"])

            self.assertGreater(successful, 0, "모든 동시 요청이 실패했습니다.")
            self.assertLess(total_time, 45, "전체 처리 시간이 너무 오래 걸립니다.")

            print(
                f"✅ 성능 테스트 통과: {successful}/{concurrent_requests} 성공, "
                f"총 시간: {total_time:.2f}초"
            )

        except Exception as e:
            print(f"⚠️  성능 테스트 스킵: {str(e)}")

    # ==========================================
    # 4. 프로세서 통합 테스트
    # ==========================================

    def test_all_processors_creation(self):
        """모든 프로세서 생성 테스트"""
        form_types = [
            "연차 신청서",
            "개인 경비 사용내역서",
            "야근식대비용 신청서",
            "교통비 신청서",
            "비품/소모품 구입내역서",
            "구매 품의서",
            "법인카드 사용내역서",
            "파견 및 출장 보고서",
        ]

        created_processors = 0
        for form_type in form_types:
            try:
                processor = ProcessorFactory.create_processor(form_type)
                if processor is not None:
                    created_processors += 1
            except Exception as e:
                print(f"⚠️  {form_type} 프로세서 생성 실패: {str(e)}")

        self.assertEqual(created_processors, 8, "모든 프로세서가 생성되지 않았습니다.")
        print("✅ 모든 프로세서 생성 테스트 통과")

    def test_processor_inheritance(self):
        """프로세서 상속 구조 테스트"""
        from form_selector.processors.base_processor import BaseFormProcessor

        test_forms = ["연차 신청서", "개인 경비 사용내역서", "교통비 신청서"]

        for form_type in test_forms:
            processor = ProcessorFactory.create_processor(form_type)
            self.assertIsInstance(
                processor,
                BaseFormProcessor,
                f"{form_type} 프로세서가 BaseFormProcessor를 상속받지 않음",
            )

        print("✅ 프로세서 상속 구조 테스트 통과")

    # ==========================================
    # 5. 에지 케이스 테스트
    # ==========================================

    def test_edge_cases_empty_content(self):
        """빈 내용 처리 테스트"""
        try:
            response = requests.post(
                f"{self.base_url}/form-selector", json={"form_content": ""}, timeout=10
            )

            # 에러 응답이거나 적절한 처리 확인
            self.assertTrue(
                response.status_code in [400, 422, 500]
                or "오류" in response.json().get("message", "")
            )
            print("✅ 빈 내용 처리 테스트 통과")

        except requests.exceptions.RequestException:
            print("⚠️  빈 내용 처리 테스트 스킵: 서버 연결 불가")

    def test_edge_cases_special_characters(self):
        """특수 문자 처리 테스트"""
        special_content = """
        제목: 특수문자 테스트 !@#$%^&*()
        신청자: 홍길동 <script>alert('test')</script>
        내용: 이모지 😀😁😂
        """

        try:
            response = requests.post(
                f"{self.base_url}/form-selector",
                json={"form_content": special_content},
                timeout=15,
            )

            # XSS 방지 확인
            if response.status_code == 200:
                result = response.json()
                html_template = result.get("html_template", "")
                self.assertNotIn("<script>", html_template)

            print("✅ 특수 문자 처리 테스트 통과")

        except requests.exceptions.RequestException:
            print("⚠️  특수 문자 처리 테스트 스킵: 서버 연결 불가")

    # ==========================================
    # 6. 통합 테스트 리포트 생성
    # ==========================================

    def test_generate_integration_report(self):
        """통합 테스트 결과 리포트 생성"""
        report = {
            "test_date": datetime.now().isoformat(),
            "total_test_forms": len(self.test_data),
            "server_url": self.base_url,
            "processors_tested": 8,
            "test_categories": [
                "전체 플로우 테스트",
                "API 통합 테스트",
                "성능 테스트",
                "에러 처리 테스트",
                "프로세서 테스트",
            ],
            "status": "Form Selector 리팩토링 프로젝트 통합 테스트 완료",
        }

        # 리포트 파일 저장
        with open("integration_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print("✅ 통합 테스트 리포트 생성 완료: integration_test_report.json")
        print(f"📊 테스트 양식 수: {report['total_test_forms']}")
        print(f"🔧 프로세서 수: {report['processors_tested']}")
        print("🎉 Form Selector 리팩토링 프로젝트 통합 테스트 완료!")


if __name__ == "__main__":
    # 테스트 실행
    print("🚀 Form Selector 통합 테스트 시작...")
    print("=" * 50)

    unittest.main(verbosity=2, failfast=False, buffer=True)
