# LLM 호출 및 템플릿 반환 서비스 함수 정의 예정
import logging  # 로깅 추가
from typing import Tuple, Dict, Any  # Tuple, Dict, Any 추가
import json  # json 모듈 추가

# llm.py에서 체인 생성 함수와 SLOT_EXTRACTOR_CHAINS를 가져옴
from .llm import get_form_classifier_chain, SLOT_EXTRACTOR_CHAINS

# form_configs.py에서 사용 가능한 양식 타입 리스트를 가져옴
from .form_configs import AVAILABLE_FORM_TYPES, TEMPLATE_FILENAME_MAP

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

# 휴가 종류 텍스트를 HTML value로 매핑
LEAVE_TYPE_TEXT_TO_VALUE_MAP = {
    "연차": "annual",
    "오전 반차": "half_day_morning",
    "오후 반차": "half_day_afternoon",
    "오전 반반차": "quarter_day_morning",
    "오후 반반차": "quarter_day_afternoon",
    "오전반차": "half_day_morning",  # 공백 없는 경우도 고려
    "오후반차": "half_day_afternoon",  # 공백 없는 경우도 고려
}


def fill_slots_in_template(
    template: str, slots_dict: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    # slots_dict는 이제 Pydantic 모델의 .model_dump() 결과일 수 있으므로, None 값 필터링이 필요할 수 있음
    logging.info(f"Initial slots_dict before any processing: {slots_dict}")

    # Pre-process all string values in slots_dict to escape backslashes for re.sub
    # This applies to single string values and strings within lists of dicts (like items)
    if slots_dict:
        processed_slots_for_re = {}
        for k, v in slots_dict.items():
            if isinstance(v, str):
                processed_slots_for_re[k] = v.replace("\\\\", "\\\\\\\\")
            elif isinstance(v, list):
                new_list = []
                for item in v:
                    if isinstance(item, dict):
                        new_dict_item = {}
                        for item_k, item_v in item.items():
                            if isinstance(item_v, str):
                                new_dict_item[item_k] = item_v.replace(
                                    "\\\\", "\\\\\\\\"
                                )
                            else:
                                new_dict_item[item_k] = item_v
                        new_list.append(new_dict_item)
                    elif isinstance(item, str):  # list of strings
                        new_list.append(item.replace("\\\\", "\\\\\\\\"))
                    else:
                        new_list.append(item)
                processed_slots_for_re[k] = new_list
            else:
                processed_slots_for_re[k] = v
        # Use these pre-processed slots for filling the template
        # Note: This logging might be very verbose if slots_dict is large
        logging.info(
            f"Slots after pre-processing backslashes for re.sub: {processed_slots_for_re}"
        )
        # The original slots_dict is passed to UI, pre-processed ones are for re.sub via processed_slots
    else:
        processed_slots_for_re = {}

    logging.info(
        f"fill_slots_in_template_called with original slots_dict: {slots_dict}"
    )  # Log original for comparison
    if not slots_dict:  # Check original slots_dict for emptiness
        return template, {}

    active_slots = {
        k: v for k, v in slots_dict.items() if v is not None
    }  # Use original slots_dict for active_slots

    # For items_json_str, use the pre-processed list if it exists, otherwise from active_slots (original)
    # And for the replacer, it should use values from a dictionary that has backslashes escaped for re.sub.
    # Let's refine `processed_slots` to be the one used by `replacer` and `items_json_str` generation.

    # Create a deep copy of active_slots to modify for re.sub compatibility
    # This will be the source for `replacer` and for `items_json_str`
    slots_for_replacer = {}
    for key, value in active_slots.items():
        if isinstance(value, str):
            slots_for_replacer[key] = value.replace("\\\\", "\\\\\\\\")
        elif isinstance(value, list) and key in [
            "items",
            "expense_items",
            "card_usage_items",
        ]:  # Assuming these are lists of dicts
            new_item_list = []
            for item_detail_dict in value:
                if isinstance(item_detail_dict, dict):
                    new_sub_dict = {}
                    for sub_k, sub_v in item_detail_dict.items():
                        if isinstance(sub_v, str):
                            new_sub_dict[sub_k] = sub_v.replace("\\\\", "\\\\\\\\")
                        else:
                            new_sub_dict[sub_k] = sub_v
                    new_item_list.append(new_sub_dict)
                else:  # Should not happen for "items" like lists based on Pydantic models
                    new_item_list.append(item_detail_dict)
            slots_for_replacer[key] = new_item_list
        else:  # Numbers, booleans, other list types not needing deep string replace
            slots_for_replacer[key] = value

    logging.info(
        f"Slots prepared for replacer (backslashes escaped): {slots_for_replacer}"
    )

    items_json_str = "null"
    item_keys_for_js = ["items", "expense_items", "card_usage_items"]

    for item_key in item_keys_for_js:
        if item_key in slots_for_replacer and isinstance(
            slots_for_replacer[item_key], list
        ):
            # items_list_of_dicts now comes from slots_for_replacer, which has strings with escaped backslashes
            items_list_of_dicts_for_json = slots_for_replacer[item_key]
            # json.dumps will handle its own escaping. The strings within items_list_of_dicts_for_json
            # are already prepared for direct inclusion if they were not part of JSON.
            # However, for JSON, we need the original unescaped (for re.sub) backslashes.
            # So, for items_json_str, we should use the original data from active_slots.

            original_items_list = active_slots.get(item_key, [])
            items_json_str = json.dumps(original_items_list, ensure_ascii=False)
            # The items_json_str itself will then be escaped by the replacer for re.sub
            logging.debug(
                f"Slot '{item_key}' (original values) will be passed to JS as JSON: {items_json_str}"
            )
            break

    # The processed_slots used by the template for direct {{key}} replacement (not items_json)
    # should also be escaped. This is now `slots_for_replacer`.
    # Date parsing and other transformations should happen on `active_slots` or a copy,
    # and then the results also need to be escaped before being put into `slots_for_replacer`.

    # Perform transformations (like date parsing) on a copy of active_slots first
    transformed_slots = {**active_slots}

    # Process items specifically for purchase_approval_form related keys
    if "items" in transformed_slots and isinstance(transformed_slots["items"], list):
        updated_items = []
        for item in transformed_slots["items"]:
            if isinstance(item, dict):
                processed_item = {**item}  # Make a copy to modify

                # Handle item_delivery_request_date -> item_delivery_date
                if "item_delivery_request_date" in processed_item and isinstance(
                    processed_item["item_delivery_request_date"], str
                ):
                    parsed_date = parse_relative_date_to_iso(
                        processed_item["item_delivery_request_date"]
                    )
                    if parsed_date:
                        processed_item["item_delivery_date"] = parsed_date
                        logging.debug(
                            f"Item's 'item_delivery_request_date' ('{processed_item['item_delivery_request_date']}') parsed to 'item_delivery_date': '{parsed_date}'"
                        )
                    else:
                        logging.warning(
                            f"Failed to parse item_delivery_request_date: {processed_item['item_delivery_request_date']}. Keeping original if item_delivery_date not present."
                        )
                        if "item_delivery_date" not in processed_item:
                            processed_item["item_delivery_date"] = processed_item[
                                "item_delivery_request_date"
                            ]
                    if (
                        "item_delivery_request_date" in processed_item
                        and "item_delivery_date" in processed_item
                        and processed_item["item_delivery_request_date"]
                        != processed_item["item_delivery_date"]
                    ):
                        del processed_item["item_delivery_request_date"]

                # Handle item_purpose -> item_notes
                if "item_purpose" in processed_item:
                    if (
                        "item_notes" not in processed_item
                        or not processed_item["item_notes"]
                    ):
                        processed_item["item_notes"] = processed_item["item_purpose"]
                        logging.debug(
                            f"Item's 'item_purpose' ('{processed_item['item_purpose']}') mapped to 'item_notes'"
                        )
                        if (
                            "item_purpose" in processed_item
                            and "item_notes" in processed_item
                            and processed_item["item_purpose"]
                            == processed_item["item_notes"]
                        ):
                            del processed_item["item_purpose"]
                    elif processed_item["item_purpose"] != processed_item["item_notes"]:
                        logging.debug(
                            f"Item's 'item_purpose' ('{processed_item['item_purpose']}') not mapped to 'item_notes' as 'item_notes' already exists with value: '{processed_item['item_notes']}'"
                        )
                updated_items.append(processed_item)
            else:
                updated_items.append(item)
        transformed_slots["items"] = updated_items
        logging.info(
            f"Items list processed for date and purpose mapping: {transformed_slots['items']}"
        )

    # --- START: Process expense_items for dates ---
    if "expense_items" in transformed_slots and isinstance(
        transformed_slots["expense_items"], list
    ):
        updated_expense_items = []
        for item in transformed_slots["expense_items"]:
            if isinstance(item, dict):
                processed_item = {**item}
                if "expense_date" in processed_item and isinstance(
                    processed_item["expense_date"], str
                ):
                    original_date_str = processed_item["expense_date"]
                    parsed_date = parse_relative_date_to_iso(original_date_str)
                    if parsed_date:
                        processed_item["expense_date"] = parsed_date
                        logging.debug(
                            f"Expense item's 'expense_date' ('{original_date_str}') parsed to '{parsed_date}'"
                        )
                    else:
                        logging.warning(
                            f"Failed to parse expense_date: {original_date_str}. Keeping original."
                        )
                updated_expense_items.append(processed_item)
            else:
                updated_expense_items.append(item)
        transformed_slots["expense_items"] = updated_expense_items
        logging.info(
            f"Expense items list processed for dates: {transformed_slots.get('expense_items')}"
        )
    # --- END: Process expense_items for dates ---

    # --- START: Process card_usage_items for dates ---
    if "card_usage_items" in transformed_slots and isinstance(
        transformed_slots["card_usage_items"], list
    ):
        updated_card_items = []
        for item in transformed_slots["card_usage_items"]:
            if isinstance(item, dict):
                processed_item = {**item}
                if "usage_date" in processed_item and isinstance(
                    processed_item["usage_date"], str
                ):
                    original_date_str = processed_item["usage_date"]
                    parsed_date = parse_relative_date_to_iso(original_date_str)
                    if parsed_date:
                        processed_item["usage_date"] = parsed_date
                        logging.debug(
                            f"Card usage item's 'usage_date' ('{original_date_str}') parsed to '{parsed_date}'"
                        )
                    else:
                        logging.warning(
                            f"Failed to parse usage_date: {original_date_str}. Keeping original."
                        )
                updated_card_items.append(processed_item)
            else:
                updated_card_items.append(item)
        transformed_slots["card_usage_items"] = updated_card_items
        logging.info(
            f"Card usage items list processed for dates: {transformed_slots.get('card_usage_items')}"
        )
    # --- END: Process card_usage_items for dates ---

    if "leave_type" in transformed_slots and isinstance(
        transformed_slots["leave_type"], str
    ):
        leave_type_text = transformed_slots["leave_type"]
        if leave_type_text in LEAVE_TYPE_TEXT_TO_VALUE_MAP:
            transformed_slots["leave_type"] = LEAVE_TYPE_TEXT_TO_VALUE_MAP[
                leave_type_text
            ]
            logging.debug(
                f"Slot 'leave_type' preprocessed: '{leave_type_text}' -> '{transformed_slots['leave_type']}'"
            )
        else:
            logging.warning(
                f"Slot 'leave_type' text '{leave_type_text}' not found in LEAVE_TYPE_TEXT_TO_VALUE_MAP. Keeping original."
            )

    if "overtime_ampm" in transformed_slots and isinstance(
        transformed_slots["overtime_ampm"], str
    ):
        ampm_value_original = transformed_slots["overtime_ampm"]
        ampm_value_upper = ampm_value_original.upper()
        if (
            "밤" in ampm_value_original
            or "오후" in ampm_value_original
            or "P" in ampm_value_upper
        ):
            transformed_slots["overtime_ampm"] = "PM"
        elif (
            "새벽" in ampm_value_original
            or "오전" in ampm_value_original
            or "A" in ampm_value_upper
        ):
            transformed_slots["overtime_ampm"] = "AM"
        # else: 정확히 매칭되지 않으면 원본 값을 유지하거나, 기본값(예: "PM")으로 설정 가능
        # 현재는 매칭 안되면 원본 유지 (HTML option에 해당 값이 없을 수 있음 주의)
        logging.debug(
            f"Slot 'overtime_ampm' preprocessed: '{ampm_value_original}' -> '{transformed_slots['overtime_ampm']}'"
        )

    for key, value in active_slots.items():
        logging.debug(f"Processing slot - Key: {key}, Value: {value}")
        if isinstance(value, str):
            original_value_for_logging = value

            # 이미 overtime_ampm 및 leave_type은 위에서 처리되었으므로, 여기서는 건너뜀
            if key == "overtime_ampm" or key == "leave_type":
                continue

            if key == "meeting_datetime" or key == "meeting_time":
                parsed_datetime = parse_datetime_description_to_iso_local(value)
                if parsed_datetime:
                    transformed_slots[key] = parsed_datetime
                    logging.debug(
                        f"Datetime slot '{key}' processed: '{original_value_for_logging}' -> '{transformed_slots[key]}'"
                    )
                continue
            elif key == "meeting_time_description":
                parsed_datetime = parse_datetime_description_to_iso_local(value)
                if parsed_datetime:
                    transformed_slots["meeting_datetime"] = parsed_datetime
                    logging.debug(
                        f"Datetime slot '{key}' (-> meeting_datetime) processed: '{original_value_for_logging}' -> '{transformed_slots['meeting_datetime']}'"
                    )
                continue

            key_lower = key.lower()
            is_date_slot = any(
                substring in key_lower for substring in DATE_SLOT_KEY_SUBSTRINGS
            )
            if is_date_slot:
                # parse_relative_date_to_iso가 None을 반환할 수 있으므로, 그 경우 원본 값을 유지할지 결정 필요
                # 여기서는 파싱 성공 시에만 값을 업데이트하고, 실패 시 transformed_slots에는 active_slots의 원본 값이 남아있음.

                # Skip if key is within an item dictionary as it's handled above for 'items' list
                # This general date parsing should not re-process item dates if already handled.
                # A more robust way would be to check if the value being processed is part of an item,
                # but for now, a simple key name check might suffice if item date keys are specific.
                # Example: if key.startswith("item_") and "date" in key: continue
                # However, the new logic for 'items' processes them before this loop, so this should be fine.

                parsed_date = parse_relative_date_to_iso(value)
                if parsed_date is not None:  # 파싱 성공 시에만 업데이트
                    transformed_slots[key] = parsed_date
                    logging.debug(
                        f"Date slot '{key}' processed: '{original_value_for_logging}' -> '{transformed_slots[key]}'"
                    )
                else:  # 파싱 실패 시 (None 반환)
                    logging.warning(
                        f"Date slot '{key}' parsing failed for value: '{original_value_for_logging}'. Keeping original."
                    )
                    # transformed_slots[key]는 이미 active_slots로부터 원본값을 가지고 있음

    logging.info(
        f"Final slots prepared for replacer after transformations: {transformed_slots}"
    )

    # --- START: items_json_str 생성 로직 이동 및 수정 ---
    items_json_str = "null"
    item_keys_for_js = ["items", "expense_items", "card_usage_items"]

    for item_key in item_keys_for_js:
        # 이제 transformed_slots에서 아이템 리스트를 가져옵니다.
        # slots_for_replacer는 re.sub를 위한 백슬래시 이스케이프된 버전이므로 여기서는 사용하지 않습니다.
        # items_json_str에 들어갈 데이터는 최종 변환된(날짜 파싱 등) 순수 데이터여야 합니다.
        if item_key in transformed_slots and isinstance(
            transformed_slots[item_key], list
        ):
            # transformed_slots에서 가져온, 모든 변환이 완료된 아이템 리스트
            final_items_list_for_json = transformed_slots.get(item_key, [])
            items_json_str = json.dumps(final_items_list_for_json, ensure_ascii=False)
            logging.debug(
                f"Slot '{item_key}' (transformed values) will be passed to JS as JSON: {items_json_str}"
            )
            break
    # --- END: items_json_str 생성 로직 이동 및 수정 ---

    logging.info(
        f"Attempting to fill template. items_json_str value is: {items_json_str[:200]}"
    )  # items_json_str 값 확인
    logging.info(f"Template before re.sub (first 300 chars): {template[:300]}")

    def replacer(match):
        key_in_template = match.group(1)
        if key_in_template == "items_json":
            # items_json_str은 이미 json.dumps로 생성된 올바른 JSON 문자열이므로,
            # 추가적인 백슬래시 이스케이프 없이 그대로 반환합니다.
            return items_json_str

        value_to_return = transformed_slots.get(key_in_template, "")
        # Values in transformed_slots (if strings) are already escaped.
        # If not string, convert to string.
        return (
            str(value_to_return)
            if not isinstance(value_to_return, str)
            else value_to_return
        )

    # {key} 형태의 플레이스홀더를 찾도록 수정합니다. \w+는 items_json (언더스코어 포함)을 포함합니다.
    filled_template = re.sub(r"{(\w+)}", replacer, template)

    logging.info(
        f"Template after re.sub (first 300 chars of filled_template): {filled_template[:300]}"
    )

    return (
        filled_template,
        transformed_slots,
    )


def classify_and_extract_slots_for_template(user_input: UserInput) -> Dict[str, Any]:
    # 1단계: 양식 분류 및 키워드 추출
    form_classifier_chain = get_form_classifier_chain()
    try:
        classifier_result = form_classifier_chain.invoke({"input": user_input.input})
        logging.info(f"Classifier result: {classifier_result}")
        if (
            not classifier_result
            or not hasattr(classifier_result, "form_type")
            or not classifier_result.form_type
        ):
            # form_type이 비어있는 경우도 실패로 간주
            raise OutputParserException(
                "Form type not found or empty in classifier output."
            )
    except OutputParserException as e:
        logging.error(f"Form classification parsing failed: {e}")
        return {
            "error": "CLASSIFICATION_FAILED",
            "message_to_user": "죄송합니다, 요청하신 내용을 정확히 이해하지 못했습니다. 어떤 종류의 문서를 찾으시나요?",
            "available_forms": AVAILABLE_FORM_TYPES,  # form_configs.py 에서 가져옴
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

    # 분류된 form_type이 AVAILABLE_FORM_TYPES에 있는지 확인 (선택적 방어 코드)
    if form_type not in AVAILABLE_FORM_TYPES:
        logging.warning(
            f"Unknown form_type classified: {form_type}. Available: {AVAILABLE_FORM_TYPES}"
        )
        return {
            "error": "UNKNOWN_FORM_TYPE_CLASSIFIED",
            "message_to_user": f"죄송합니다. 현재 지원하지 않는 문서 종류('{form_type}')입니다. 다음 중에서 선택해 주세요.",
            "available_forms": AVAILABLE_FORM_TYPES,
            "original_input": user_input.input,
        }

    # 2단계: HTML 템플릿 검색
    # retrieve_template 함수는 form_type (예: "연차 신청서")을 직접 사용합니다.
    retrieved_template_html = retrieve_template(form_type=form_type, keywords=keywords)

    if not retrieved_template_html:
        logging.warning(
            f"Template not found for form_type: {form_type} with keywords: {keywords}"
        )
        # TEMPLATE_FILENAME_MAP을 사용하여 파일 존재 여부라도 확인해볼 수 있지만, retrieve_template 실패 시 일단 에러 반환
        return {
            "error": "TEMPLATE_NOT_FOUND",
            "message_to_user": f"'{form_type}' 양식의 내용을 가져올 수 없습니다. 관리자에게 문의하거나 다른 양식을 선택해주세요.",
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

                # "회의비 지출결의서"의 경우 "지출 내역" 조합 (기존 로직 유지)
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
                        if venue_fee or refreshment_fee:
                            expense_details_parts.append(
                                f"기타 상세: {llm_expense_details}"
                            )
                        else:
                            expense_details_parts.append(llm_expense_details)

                    if expense_details_parts:
                        raw_slots["expenses"] = ", ".join(expense_details_parts)
                        logging.info(
                            f"Combined 'expenses' for meeting_expense: {raw_slots['expenses']}"
                        )
                    elif raw_slots.get("amount") and not expense_details_parts:
                        # amount만 있고 다른 상세 항목이 없을 때 expenses 채우기
                        raw_slots["expenses"] = f"총 지출: {raw_slots.get('amount')}"
                        logging.info(
                            f"Using total amount for 'expenses': {raw_slots['expenses']}"
                        )
            else:
                logging.warning(f"Slot extraction returned None for {form_type}")
        except OutputParserException as e:
            logging.error(f"Slot extraction parsing failed for {form_type}: {e}")
        except Exception as e:
            logging.error(
                f"Slot extraction failed with an unexpected error for {form_type}: {e}",
                exc_info=True,
            )
    else:
        logging.warning(f"No slot extractor chain found for form_type: {form_type}")

    # 4단계: 슬롯 값 변환 및 HTML 템플릿 채우기
    final_html, final_processed_slots = fill_slots_in_template(
        retrieved_template_html, raw_slots
    )
    logging.info(f"Final processed slots: {final_processed_slots}")
    # logging.info(f"Final HTML template: {final_html[:500]}...") # 너무 길면 일부만 로깅

    return {
        "form_type": form_type,
        "keywords": keywords,
        "slots": final_processed_slots,  # 최종적으로 변환되고 채워진 슬롯
        "html_template": final_html,
        "original_input": user_input.input,
    }


# 기존 classify_and_get_template 함수는 classify_and_extract_slots_for_template로 대체됨.
