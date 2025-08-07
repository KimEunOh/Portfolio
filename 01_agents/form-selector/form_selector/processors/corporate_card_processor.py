"""법인카드 지출내역서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor
import logging
import json
from datetime import datetime
from ..utils import parse_relative_date_to_iso, convert_keys_to_camel


class CorporateCardProcessor(BaseFormProcessor):
    """법인카드 지출내역서 전용 프로세서

    - 복잡한 사용 내역 구조 처리 (최대 6개)
    - 카테고리 매핑 (한국어 → 영어)
    - 이중 총액 계산 (total_amount_header, total_usage_amount)
    - 5개 필드 per 사용내역: usage_date, usage_category, merchant_name, usage_amount, usage_notes
    """

    # 카테고리 매핑 테이블
    CATEGORY_MAPPING = {
        # 식대/회식비
        "meals": "meals",
        "식대": "meals",
        "회식": "meals",
        "커피": "meals",
        "음료": "meals",
        "식당": "meals",
        "카페": "meals",
        "스타벅스": "meals",
        # 교통/운반비
        "traffic_transport": "traffic_transport",
        "교통비": "traffic_transport",
        "주차비": "traffic_transport",
        "택시": "traffic_transport",
        "버스": "traffic_transport",
        "지하철": "traffic_transport",
        "주유비": "traffic_transport",
        "운반비": "traffic_transport",
        "배송비": "traffic_transport",
        # 사무용품비
        "supplies": "supplies",
        "사무용품": "supplies",
        "문구류": "supplies",
        "용지": "supplies",
        "펜": "supplies",
        "노트북": "supplies",
        "컴퓨터": "supplies",
        "비품": "supplies",
        # 접대비
        "entertainment": "entertainment",
        "접대비": "entertainment",
        "거래처": "entertainment",
        "고객": "entertainment",
        "미팅": "entertainment",
        "골프": "entertainment",
        # 공과금
        "utility": "utility",
        "공과금": "utility",
        "전기료": "utility",
        "수도료": "utility",
        "인터넷": "utility",
        "통신비": "utility",
        "전화료": "utility",
        # 복리후생비
        "welfare": "welfare",
        "복리후생": "welfare",
        "직원": "welfare",
        "복지": "welfare",
        "건강검진": "welfare",
        "워크샵": "welfare",
        # 교육훈련비
        "education": "education",
        "교육": "education",
        "세미나": "education",
        "강의": "education",
        "연수": "education",
        "자격증": "education",
        "도서": "education",
        # 기타
        "other": "other",
        "기타": "other",
    }

    def preprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """법인카드 사용 내역서 전처리"""
        # card_usage_items가 있고 statement_date가 없는 경우, 첫 아이템 날짜로 채움
        if (
            "card_usage_items" in slots
            and slots["card_usage_items"]
            and not slots.get("statement_date")
        ):
            first_item = slots["card_usage_items"][0]
            if "usage_date" in first_item and first_item["usage_date"]:
                slots["statement_date"] = first_item["usage_date"]
                logging.info(
                    f"preprocess_slots: Set statement_date to {first_item['usage_date']} from the first card usage item."
                )
        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """사용 내역 처리: card_usage_items 배열을 HTML 필드로 분해하고 총액 계산"""
        result = slots.copy()

        # 총액 초기화
        total_amount = 0

        # card_usage_items 배열이 있는 경우 HTML 필드로 분해
        if "card_usage_items" in slots and slots["card_usage_items"]:
            items = slots["card_usage_items"]

            # 최대 6개 사용 내역까지 처리
            for i, item in enumerate(items[:6], 1):
                result[f"usage_date_{i}"] = item.get("usage_date", "")

                # 카테고리 매핑
                raw_category = item.get("usage_category", "")
                mapped_category = self.convert_category(raw_category)
                result[f"usage_category_{i}"] = mapped_category

                # usage_description을 merchant_name으로 매핑
                result[f"merchant_name_{i}"] = item.get("usage_description", "")
                result[f"usage_amount_{i}"] = item.get("usage_amount", 0)
                result[f"usage_notes_{i}"] = item.get("usage_notes", "")

                # 총액 계산
                total_amount += item.get("usage_amount", 0) or 0

            # 처리된 아이템 리스트를 다시 슬롯에 포함
            result["card_usage_items"] = items

        # 총액 설정 (두 개 필드 동기화)
        if "total_amount_header" in slots and slots["total_amount_header"] is not None:
            # 직접 제공된 값 우선 사용
            result["total_amount_header"] = slots["total_amount_header"]
            result["total_usage_amount"] = slots["total_amount_header"]
        else:
            # 계산된 총액 사용
            result["total_amount_header"] = total_amount
            result["total_usage_amount"] = total_amount

        return result

    def convert_category(self, category: str) -> str:
        """카테고리 매핑: 한국어나 자연어를 영어 카테고리로 변환"""
        if not category:
            return "other"

        category_lower = category.lower().strip()

        # 직접 매핑
        if category_lower in self.CATEGORY_MAPPING:
            return self.CATEGORY_MAPPING[category_lower]

        # 부분 문자열 매칭
        for key, value in self.CATEGORY_MAPPING.items():
            if key in category_lower or category_lower in key:
                return value

        # 매핑되지 않으면 기타로 분류
        return "other"

    def convert_category_to_korean(self, english_category: str) -> str:
        """영어 카테고리를 한글 분류로 변환 (API 전송용)"""
        korean_mapping = {
            "meals": "식대",
            "traffic_transport": "교통비",
            "supplies": "소모품비",
            "entertainment": "접대비",
            "utility": "공과금",
            "welfare": "복리후생비",
            "education": "교육훈련비",
            "other": "기타",
        }
        return korean_mapping.get(english_category, "기타")

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """필드 변환: 특별한 필드 변환 없음"""
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """법인카드 사용 내역서 후처리"""
        return slots

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """법인카드 지출내역서 폼 데이터를 API Payload로 변환"""
        logging.info("CorporateCardProcessor: Converting form data to API payload")

        # 1. form_data에서 필요한 데이터를 snake_case 키로 가져옵니다.
        doc_cn_reason = form_data.get("expense_reason", "법인카드 사용 내역서")
        items_snake = form_data.get("card_usage_items", [])

        # 2. items 리스트의 키를 camelCase로 변환합니다.
        items_camel = convert_keys_to_camel(items_snake)

        # 3. 변환된 데이터를 사용하여 apdInfo JSON 문자열을 생성합니다.
        apd_info_dict = {
            "cardNumber": form_data.get("card_number", ""),
            "expenseReason": doc_cn_reason,
            "statementDate": form_data.get("statement_date", ""),
            "totalAmount": int(form_data.get("total_usage_amount", 0) or 0),
        }
        final_apd_info_str = json.dumps(
            convert_keys_to_camel(apd_info_dict), ensure_ascii=False
        )

        # 4. 기본 페이로드 구조를 설정합니다.
        payload = {
            "mstPid": "9",
            "aprvNm": "법인카드 지출내역서",
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": doc_cn_reason,
            "apdInfo": final_apd_info_str,
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # 5. amountList를 구성합니다. (camelCase로 변환된 items_camel 사용)
        if items_camel:
            for item in items_camel:
                usage_date = item.get("usageDate")
                if not usage_date or "SLOT_NOT_FOUND" in usage_date:
                    continue

                usage_amount = item.get("usageAmount", 0)
                raw_category = item.get("usageCategory", "기타")

                # 1. 자동 분류용으로 영어 카테고리 변환 (기존 로직 유지)
                english_category = self.convert_category(raw_category)

                # 2. API 전송용으로 한글 분류 변환
                korean_category = self.convert_category_to_korean(english_category)

                adit_info = {"notes": item.get("usageNotes", "")}

                payload["amountList"].append(
                    {
                        "useYmd": usage_date,
                        "dvNm": korean_category,  # 한글 분류로 API 전송
                        "useRsn": item.get("usageDescription", ""),  # 상점명
                        "qnty": 1,
                        "amt": int(usage_amount) if str(usage_amount).isdigit() else 0,
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )
        else:
            # Fallback for older format (HTML 필드 직접 참조)
            # 이 부분의 키들도 service.py에 의해 camelCase로 변환되었을 가능성이 있으므로 camelCase로 참조
            for i in range(1, 7):
                usage_date = form_data.get(f"usageDate_{i}")
                if not usage_date or "SLOT_NOT_FOUND" in usage_date:
                    continue

                usage_amount = form_data.get(f"usageAmount_{i}", 0)
                adit_info = {"notes": form_data.get(f"usageNotes_{i}", "")}

                payload["amountList"].append(
                    {
                        "useYmd": usage_date,
                        "dvNm": form_data.get(
                            f"usageCategory_{i}", "기타"
                        ),  # 이미 한글 분류
                        "useRsn": form_data.get(f"merchantName_{i}", ""),
                        "qnty": 1,
                        "amt": int(usage_amount) if str(usage_amount).isdigit() else 0,
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )

        # 결재라인 정보 추가
        if "approvers" in form_data and form_data["approvers"]:
            for approver in form_data["approvers"]:
                payload["lineList"].append(
                    {
                        "aprvPsId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("CorporateCardProcessor: API payload conversion completed")
        return payload
