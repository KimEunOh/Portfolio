# LLM 호출 및 템플릿 반환 서비스 함수 정의 예정
import logging  # 로깅 추가
from typing import Tuple, Dict, Any  # Tuple, Dict, Any 추가
from .llm import get_form_classifier_chain, SLOT_EXTRACTOR_CHAINS, AVAILABLE_FORM_TYPES
from .schema import (
    UserInput,
)  # FormClassifierOutput 등은 llm.py에서 처리 후 Python 객체로 넘어오므로 직접 여기서 사용 X
from .utils import (
    parse_relative_date_to_iso,
    parse_datetime_description_to_iso_local,
)  # utils 모듈에서 함수 임포트
from .rag import retrieve_template  # RAG 모듈의 retrieve_template 함수 임포트
import re
from langchain_core.exceptions import OutputParserException

# 날짜 관련 슬롯 키 이름에 포함될 수 있는 문자열 리스트
DATE_SLOT_KEY_SUBSTRINGS = ["date", "일자", "기간"]


def fill_slots_in_template(
    template: str, slots_dict: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    # slots_dict는 이제 Pydantic 모델의 .model_dump() 결과일 수 있으므로, None 값 필터링이 필요할 수 있음
    logging.info(f"fill_slots_in_template_called with slots_dict: {slots_dict}")
    if not slots_dict:
        return template, {}

    # None 값을 가진 키는 아예 제거하거나, 빈 문자열로 처리할 수 있습니다.
    # 여기서는 None이 아닌 값만 사용하도록 필터링합니다.
    # 또는 Pydantic 모델에서 `exclude_none=True`를 사용하여 dump 할 수도 있습니다.
    # 여기서는 명시적으로 None 값을 가진 슬롯을 처리합니다.
    active_slots = {k: v for k, v in slots_dict.items() if v is not None}

    # processed_slots는 실제 파싱/변환된 값을 담습니다.
    processed_slots = {**active_slots}

    for key, value in active_slots.items():  # None이 아닌 슬롯만 순회
        logging.debug(f"Processing slot - Key: {key}, Value: {value}")
        if isinstance(value, str):  # 문자열 값만 처리
            original_value_for_logging = value

            # 키 이름에 따른 파싱 로직 (기존 로직 활용)
            # meeting_datetime 또는 meeting_time 키는 우선적으로 datetime 파서 사용
            if key == "meeting_datetime" or key == "meeting_time":
                parsed_datetime = parse_datetime_description_to_iso_local(value)
                if parsed_datetime:
                    processed_slots[key] = parsed_datetime
                    logging.debug(
                        f"Datetime slot '{key}' processed: '{original_value_for_logging}' -> '{processed_slots[key]}'"
                    )
                # 파싱 실패 시 원본 값 유지 (processed_slots에는 이미 original_value_for_logging이 들어있음)
                # else:
                #     logging.debug(f"Datetime slot '{key}' ('{original_value_for_logging}') parsing failed, keeping original.")
                continue

            # 그 외 날짜 관련 키워드가 포함된 경우 date 파서 사용
            key_lower = key.lower()
            is_date_slot = any(
                substring in key_lower for substring in DATE_SLOT_KEY_SUBSTRINGS
            )
            if is_date_slot:
                processed_slots[key] = parse_relative_date_to_iso(value)
                logging.debug(
                    f"Date slot '{key}' processed: '{original_value_for_logging}' -> '{processed_slots[key]}'"
                )
        # else: value가 문자열이 아닌 경우 (예: Pydantic 모델에서 다른 타입으로 정의된 경우)는 그대로 둠

    logging.info(f"Processed slots for template filling: {processed_slots}")

    def replacer(match):
        key_in_template = match.group(1)
        # processed_slots에 키가 없으면 (예: 파싱 실패로 None이 되어 active_slots에서 제외된 경우)
        # 또는 원래부터 슬롯에 값이 없었던 경우 -> 빈 문자열로 치환하거나, 템플릿의 플레이스홀더를 그대로 둠
        # 여기서는 키가 없으면 빈 문자열로 채워 HTML이 깨지지 않도록 함.
        return processed_slots.get(key_in_template, "")  # 기본값을 빈 문자열로 변경

    filled_template = re.sub(r"\{(\w+)\}", replacer, template)
    # 최종적으로 UI에 전달할 슬롯 정보는 파싱/변환된 processed_slots입니다.
    return filled_template, processed_slots


def classify_and_extract_slots_for_template(user_input: UserInput) -> Dict[str, Any]:
    # 1단계: 양식 분류 및 키워드 추출
    form_classifier_chain = get_form_classifier_chain()
    try:
        classifier_result = form_classifier_chain.invoke({"input": user_input.input})
        logging.info(f"Classifier result: {classifier_result}")
        if not classifier_result or not hasattr(classifier_result, "form_type"):
            raise OutputParserException("Form type not found in classifier output.")
    except OutputParserException as e:
        logging.error(f"Form classification parsing failed: {e}")
        return {
            "error": "CLASSIFICATION_FAILED",
            "message_to_user": "죄송합니다, 요청하신 내용을 정확히 이해하지 못했습니다. 어떤 종류의 문서를 찾으시나요?",
            "available_forms": AVAILABLE_FORM_TYPES,  # llm.py 에서 가져옴
            "original_input": user_input.input,
        }
    except Exception as e:  # 다른 예외 (API 오류 등)
        logging.error(
            f"Form classification failed with an unexpected error: {e}", exc_info=True
        )
        return {
            "error": "CLASSIFICATION_UNEXPECTED_ERROR",
            "message_to_user": "양식 분류 중 오류가 발생했습니다. 다시 시도해주세요.",
            "original_input": user_input.input,
        }

    form_type = classifier_result.form_type
    keywords = (
        classifier_result.keywords if hasattr(classifier_result, "keywords") else []
    )

    # 2단계: HTML 템플릿 검색
    retrieved_template_html = retrieve_template(form_type=form_type, keywords=keywords)
    if not retrieved_template_html:
        logging.warning(
            f"Template not found for form_type: {form_type} with keywords: {keywords}"
        )
        return {
            "error": "TEMPLATE_NOT_FOUND",
            "message_to_user": f"'{form_type}' 양식을 찾을 수 없습니다. 다른 양식을 선택하거나 요청을 더 자세히 작성해주세요.",
            "form_type": form_type,
            "keywords": keywords,
            "original_input": user_input.input,
            "available_forms": AVAILABLE_FORM_TYPES,
        }
    logging.info(f"Retrieved template for form_type: {form_type}")

    # 3단계: 양식별 슬롯 추출
    raw_slots: Dict[str, Any] = (
        {}
    )  # LLM이 추출한 원본 슬롯 (Pydantic 모델 객체 -> dict)
    if form_type in SLOT_EXTRACTOR_CHAINS:
        slot_chain = SLOT_EXTRACTOR_CHAINS[form_type]
        try:
            # 슬롯 추출 LLM은 Pydantic 모델 객체를 반환
            extracted_slots_model = slot_chain.invoke({"input": user_input.input})
            logging.info(
                f"Extracted slots model for {form_type}: {extracted_slots_model}"
            )
            if extracted_slots_model:
                # Pydantic 모델을 딕셔너리로 변환 (None 값 포함 가능, fill_slots_in_template에서 처리)
                raw_slots = extracted_slots_model.model_dump()

                # "회의비 지출결의서"의 경우 "지출 내역" 조합
                if form_type == "회의비 지출결의서":
                    expense_details_parts = []
                    venue_fee = raw_slots.get("venue_fee")
                    refreshment_fee = raw_slots.get("refreshment_fee")
                    llm_expense_details = raw_slots.get("expense_details")

                    if venue_fee:
                        expense_details_parts.append(f"회의실 대관료: {venue_fee}")
                    if refreshment_fee:
                        expense_details_parts.append(f"다과비: {refreshment_fee}")

                    if llm_expense_details:
                        # venue_fee 또는 refreshment_fee와 내용이 중복되지 않도록 고려
                        # 여기서는 llm_expense_details를 그대로 추가하거나, 다른 항목이 없을 때만 추가하는 방식 등을 선택할 수 있음.
                        # 현재는 다른 항목이 있더라도 '기타 상세:' 등으로 추가.
                        if venue_fee or refreshment_fee:
                            expense_details_parts.append(
                                f"기타 상세: {llm_expense_details}"
                            )
                        else:
                            expense_details_parts.append(
                                llm_expense_details
                            )  # 다른 항목 없으면 이것만

                    if expense_details_parts:
                        raw_slots["expenses"] = ", ".join(expense_details_parts)
                        logging.info(
                            f"Combined 'expenses' for meeting_expense: {raw_slots['expenses']}"
                        )
                    elif raw_slots.get("amount") and not expense_details_parts:
                        raw_slots["expenses"] = f"총 지출: {raw_slots.get('amount')}"
                        logging.info(
                            f"Using total amount for 'expenses': {raw_slots['expenses']}"
                        )
            else:  # LLM이 None을 반환했거나, 파싱 실패 (PydanticOutputParser가 에러를 발생시키지 않고 None을 반환하는 경우)
                logging.warning(f"Slot extraction returned None for {form_type}")
                # 이 경우 raw_slots는 빈 딕셔너리로 유지됨
        except OutputParserException as e:
            logging.error(f"Slot extraction parsing failed for {form_type}: {e}")
            # 슬롯 추출 실패 시에도 계속 진행하되, 슬롯은 비어있을 수 있음
            # 또는 여기서 에러를 반환할 수도 있음
            # 여기서는 일단 비어있는 슬롯으로 진행
        except Exception as e:
            logging.error(
                f"Slot extraction failed with an unexpected error for {form_type}: {e}",
                exc_info=True,
            )
            # 마찬가지로 비어있는 슬롯으로 진행
    else:
        logging.warning(f"No slot extractor chain found for form_type: {form_type}")
        # 이 경우 raw_slots는 빈 딕셔너리로 유지됨

    # 4단계: 슬롯 값 변환 및 HTML 템플릿 채우기
    # fill_slots_in_template는 변환된 슬롯 딕셔너리도 반환 (final_processed_slots)
    final_html, final_processed_slots = fill_slots_in_template(
        retrieved_template_html, raw_slots  # raw_slots (dict) 전달
    )
    logging.info(f"Final processed slots: {final_processed_slots}")
    logging.info(f"Final HTML template: {final_html[:200]}...")  # 너무 길면 일부만 로깅

    return {
        "form_type": form_type,
        "keywords": keywords,
        "slots": final_processed_slots,  # 최종적으로 변환되고 채워진 슬롯
        "html_template": final_html,
        "original_input": user_input.input,
    }


# 기존 classify_and_get_template 함수는 classify_and_extract_slots_for_template로 대체됨.
