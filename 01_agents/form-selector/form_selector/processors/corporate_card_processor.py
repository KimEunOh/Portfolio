"""법인카드 지출내역서 전용 프로세서"""

from typing import Dict, Any, List
from .base_processor import BaseFormProcessor
import logging
import json
from datetime import datetime
from ..utils import parse_past_date_to_iso


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
        """전처리: 기본값 설정"""
        processed = slots.copy()

        # 기본 제목 설정
        if not processed.get("title"):
            processed["title"] = "법인카드 지출내역"

        return processed

    def convert_item_dates(
        self, slots: Dict[str, Any], current_date_iso: str
    ) -> Dict[str, Any]:
        """법인카드 아이템 날짜 변환 (과거 날짜 우선)"""
        if "card_usage_items" not in slots or not isinstance(
            slots["card_usage_items"], list
        ):
            return slots

        for item in slots["card_usage_items"]:
            if "usage_date" in item and item["usage_date"]:
                item["usage_date"] = parse_past_date_to_iso(
                    item["usage_date"], current_date_iso
                )

        return slots

    def convert_items(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """사용 내역 처리: card_usage_items 배열을 HTML 필드로 분해하고 총액 계산"""
        result = slots.copy()

        # 총액 초기화
        total_amount = 0

        # card_usage_items 배열이 있는 경우 HTML 필드로 분해
        if "card_usage_items" in slots and slots["card_usage_items"]:
            usage_items = slots["card_usage_items"]

            # 최대 6개 사용 내역까지 처리
            for i, item in enumerate(usage_items[:6], 1):
                result[f"usage_date_{i}"] = item.get("usage_date", "")

                # 카테고리 매핑
                raw_category = item.get("usage_category", "")
                mapped_category = self.convert_category(raw_category)
                result[f"usage_category_{i}"] = mapped_category

                # usage_description을 merchant_name으로 매핑
                result[f"merchant_name_{i}"] = item.get("usage_description", "")
                result[f"usage_amount_{i}"] = item.get("usage_amount", 0)
                result[f"usage_notes_{i}"] = item.get("usage_notes", "")

                # 총액에 추가
                total_amount += item.get("usage_amount", 0)

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

    def convert_fields(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """필드 변환: 특별한 필드 변환 없음"""
        return slots

    def postprocess_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """후처리: 빈 필드 기본값 설정 및 지출 사유 자동 생성"""
        processed = slots.copy()

        # 기본값 설정
        if not processed.get("card_number"):
            processed["card_number"] = ""

        if not processed.get("statement_date"):
            processed["statement_date"] = datetime.now().date().isoformat()

        # 지출 사유 자동 생성
        if (
            not processed.get("expense_reason")
            and "card_usage_items" in processed
            and processed["card_usage_items"]
        ):
            categories = [
                item.get("usage_category") for item in processed["card_usage_items"]
            ]

            # 카테고리 이름 한글 매핑 (중복 제거)
            category_names_kr = {
                "meals": "식대",
                "traffic_transport": "교통비",
                "supplies": "사무용품비",
                "entertainment": "접대비",
                "utility": "공과금",
                "welfare": "복리후생비",
                "education": "교육훈련비",
                "other": "기타 경비",
            }

            unique_kr_categories = set()
            for cat in categories:
                mapped_cat = self.convert_category(cat)  # 영어 카테고리로 표준화
                if mapped_cat in category_names_kr:
                    unique_kr_categories.add(category_names_kr[mapped_cat])

            if unique_kr_categories:
                processed["expense_reason"] = (
                    ", ".join(unique_kr_categories) + " 등 사용"
                )
            else:
                processed["expense_reason"] = "법인카드 사용 내역"

        elif not processed.get("expense_reason"):
            processed["expense_reason"] = "법인카드 사용 내역"

        return processed

    def convert_to_api_payload(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """법인카드 지출내역서 폼 데이터를 API Payload로 변환"""
        logging.info("CorporateCardProcessor: Converting form data to API payload")

        # '작성 일자'가 statement_date로 넘어오므로 이를 사용
        doc_cn_reason = form_data.get("expense_reason", "법인카드 사용 내역서")

        payload = {
            "mstPid": "9",
            "aprvNm": form_data.get("title", "법인카드 사용 내역서"),
            "drafterId": form_data.get("drafterId", "00009"),
            "docCn": doc_cn_reason,
            "apdInfo": json.dumps(
                {
                    "card_number": form_data.get("card_number", ""),
                    "expense_reason": doc_cn_reason,
                    "statement_date": form_data.get("statement_date", ""),
                    "total_amount": int(form_data.get("total_usage_amount", 0) or 0),
                },
                ensure_ascii=False,
            ),
            "lineList": [],
            "dayList": [],
            "amountList": [],
        }

        # amountList 구성 (카드 사용 내역)
        if "card_usage_items" in form_data and isinstance(
            form_data["card_usage_items"], list
        ):
            for item in form_data["card_usage_items"]:
                usage_date = item.get("usage_date")
                # 유효하지 않은 항목은 건너뛰기
                if not usage_date or "SLOT_NOT_FOUND" in usage_date:
                    continue

                usage_amount = item.get("usage_amount", 0)

                # 카테고리 매핑 적용
                raw_category = item.get("usage_category", "기타")
                mapped_category = self.convert_category(raw_category)

                adit_info = {"notes": item.get("usage_notes", "")}

                payload["amountList"].append(
                    {
                        "useYmd": usage_date,
                        "dvNm": mapped_category,
                        "useRsn": item.get("usage_description", ""),  # 상점명
                        "qnty": 1,
                        "amt": int(usage_amount) if str(usage_amount).isdigit() else 0,
                        "aditInfo": json.dumps(adit_info, ensure_ascii=False),
                    }
                )
        else:
            # Fallback for older format
            for i in range(1, 7):  # 최대 6개 항목
                usage_date = form_data.get(f"usage_date_{i}")
                # 유효하지 않은 항목은 건너뛰기
                if not usage_date or "SLOT_NOT_FOUND" in usage_date:
                    continue

                usage_amount = form_data.get(f"usage_amount_{i}", 0)

                adit_info = {"notes": form_data.get(f"usage_notes_{i}", "")}

                payload["amountList"].append(
                    {
                        "useYmd": usage_date,
                        "dvNm": form_data.get(f"usage_category_{i}", "기타"),
                        "useRsn": form_data.get(f"merchant_name_{i}", ""),
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
                        "aprvPslId": approver.aprvPsId,
                        "aprvDvTy": approver.aprvDvTy,
                        "ordr": int(approver.ordr),
                    }
                )

        logging.info("CorporateCardProcessor: API payload conversion completed")
        return payload
