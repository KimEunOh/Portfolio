"""
전자결재 양식 추천 및 슬롯 자동 채우기를 위한 서비스 모듈입니다.

이 모듈은 다음의 주요 기능을 수행합니다:
- 사용자 입력을 받아 적절한 전자결재 양식을 분류합니다.
- 분류된 양식에 필요한 정보를 사용자 입력으로부터 추출(슬롯 필링)합니다.
- 추출된 정보를 HTML 템플릿에 채워 사용자에게 제공합니다.
- 상대적인 날짜 표현(예: "내일", "다음 주 월요일")을 "YYYY-MM-DD" 형식으로 변환합니다.
- 다중 항목을 포함하는 양식(예: 구매 품의서의 여러 품목)을 처리합니다.
"""

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

# 날짜 관련 슬롯의 키 이름에 포함될 수 있는 문자열 리스트입니다.
# 이 리스트에 포함된 문자열이 키 이름에 있으면 해당 슬롯 값을 날짜로 간주하고 파싱을 시도합니다.
DATE_SLOT_KEY_SUBSTRINGS = ["date", "일자", "기간"]

# LLM이 추출한 휴가 종류 텍스트(키)를 HTML <select> 요소의 option 값(value)으로 매핑합니다.
# 예를 들어, LLM이 "오전 반차"라고 추출하면, HTML에서는 "half_day_morning" 값으로 사용됩니다.
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
    """HTML 템플릿 내의 플레이스홀더를 추출된 슬롯 값으로 채웁니다.

    이 함수는 다음 주요 단계를 수행합니다:
    1.  입력된 `slots_dict`에서 None 값을 필터링하여 실제 값이 있는 활성 슬롯만 사용합니다.
    2.  슬롯 값 변환:
        *   **날짜/시간 변환**:
            *   아이템 리스트(`items`, `expense_items`, `card_usage_items`) 내의 날짜 관련 문자열
                (예: `item_delivery_request_date`, `expense_date`, `usage_date`)을 `parse_relative_date_to_iso`를
                사용하여 "YYYY-MM-DD" 형식으로 변환합니다.
            *   일반적인 날짜 슬롯 (키 이름에 `DATE_SLOT_KEY_SUBSTRINGS`의 문자열 포함 시)의 값도
                "YYYY-MM-DD" 형식으로 변환합니다.
            *   회의 시간 관련 슬롯 (`meeting_datetime`, `meeting_time`, `meeting_time_description`)은
                `parse_datetime_description_to_iso_local`을 사용하여 "YYYY-MM-DDTHH:MM" 형식으로 변환합니다.
        *   **구매 품의서 아이템 키 변경**:
            *   `items` 리스트 내 각 아이템의 `item_delivery_request_date` 키를 `item_delivery_date`로 변경합니다.
            *   `item_purpose` 키를 `item_notes`로 변경 (단, `item_notes`가 이미 존재하지 않거나 비어있을 경우).
        *   **휴가 종류 매핑**: `leave_type` 슬롯 값을 `LEAVE_TYPE_TEXT_TO_VALUE_MAP`을 참고하여 HTML `<select>` 태그의 `value`에 맞는 문자열로 변환합니다.
        *   **야근 시간 오전/오후 구분**: `overtime_ampm` 슬롯 값을 "AM" 또는 "PM"으로 표준화합니다.
    3.  **JSON 문자열 생성**: 변환이 완료된 아이템 리스트(`items`, `expense_items`, `card_usage_items` 중 하나)를
        JavaScript에서 사용할 수 있도록 `items_json_str` 이라는 JSON 문자열로 직렬화합니다.
        이 작업은 모든 슬롯 값 변환(특히 날짜 파싱)이 완료된 *후*에 수행되어, HTML의 `<input type="date">` 필드 등에
        올바른 형식의 날짜 값이 설정되도록 합니다.
    4.  **백슬래시 이스케이프 처리**: `re.sub` 함수는 백슬래시를 특별하게 취급하므로, HTML 템플릿에 삽입될 슬롯 값 중
        문자열 타입의 값들에 포함된 백슬래시를 이스케이프 처리합니다. (`value.replace("\\", "\\\\")`)
        단, `items_json_str`은 `json.dumps`를 통해 이미 올바르게 이스케이프된 JSON 문자열이므로 추가 처리를 하지 않습니다.
    5.  **플레이스홀더 치환**: `re.sub`를 사용하여 HTML 템플릿 내의 `{key}` 또는 `{items_json}` 형태의 플레이스홀더를
        처리된 슬롯 값 또는 `items_json_str`로 치환합니다.

    Args:
        template: 플레이스홀더를 포함하는 원본 HTML 템플릿 문자열.
        slots_dict: LLM으로부터 추출된 슬롯 이름과 값으로 구성된 딕셔너리.

    Returns:
        Tuple[str, Dict[str, Any]]:
            - str: 슬롯 값이 채워진 HTML 템플릿 문자열.
            - Dict[str, Any]: 최종적으로 처리된 슬롯 딕셔너리 (UI 디버그 정보 및 반환용).
    """
    logging.info(f"Initial slots_dict before any processing: {slots_dict}")

    # Pre-process all string values in slots_dict to escape backslashes for re.sub
    # This applies to single string values and strings within lists of dicts (like items)
    # re.sub의 replacer 함수에 전달될 문자열 값들은 백슬래시가 이스케이프 되어야 합니다.
    # 그렇지 않으면, 예를 들어 슬롯 값에 "C:\Users" 와 같은 경로가 있을 경우, re.sub는 이를 "C:(tab)Users"로 해석할 수 있습니다.
    if slots_dict:
        processed_slots_for_re = {}
        for k, v in slots_dict.items():
            if isinstance(v, str):
                # 단일 문자열 값의 백슬래시 이스케이프
                processed_slots_for_re[k] = v.replace("\\", "\\\\")
            elif isinstance(v, list):
                new_list = []
                for item in v:
                    if isinstance(item, dict):
                        new_dict_item = {}
                        for item_k, item_v in item.items():
                            if isinstance(item_v, str):
                                # 리스트 내 딕셔너리의 문자열 값 백슬래시 이스케이프
                                new_dict_item[item_k] = item_v.replace("\\", "\\\\")
                            else:
                                new_dict_item[item_k] = item_v
                        new_list.append(new_dict_item)
                    elif isinstance(item, str):  # list of strings
                        # 리스트 내 단순 문자열 값 백슬래시 이스케이프
                        new_list.append(item.replace("\\", "\\\\"))
                    else:
                        new_list.append(item)
                processed_slots_for_re[k] = new_list
            else:
                processed_slots_for_re[k] = v
        # logging.info(
        #     f"Slots after pre-processing backslashes for re.sub: {processed_slots_for_re}"
        # ) # 로깅이 너무 길어질 수 있어 주석 처리
    else:
        processed_slots_for_re = {}

    logging.info(
        f"fill_slots_in_template_called with original slots_dict: {slots_dict}"
    )
    if not slots_dict:
        return template, {}

    # None 값을 가진 슬롯은 템플릿 채우기에서 제외 (활성 슬롯만 사용)
    active_slots = {k: v for k, v in slots_dict.items() if v is not None}

    # `slots_for_replacer`는 `re.sub`의 `replacer` 함수 및 `items_json_str` 생성에 사용될,
    # 백슬래시가 이스케이프된 슬롯 값들을 담는 딕셔너리입니다.
    # 날짜 파싱 등의 변환은 이스케이프 전의 원본 데이터(active_slots)에 대해 수행하고,
    # 그 결과를 다시 이스케이프하여 `slots_for_replacer`에 저장합니다.
    # 하지만 현재 로직에서는 processed_slots_for_re를 사용하고, 이후 transformed_slots를 만듭니다.
    # transformed_slots가 최종적으로 re.sub에 사용되므로, 해당 값들이 이스케이프 되어야 합니다.
    # 아래에서는 transformed_slots를 기준으로 처리하고, re.sub 전달 직전에 문자열 값들을 이스케이프 합니다.

    # 모든 변환(날짜 파싱, 키 변경 등)은 active_slots의 복사본인 transformed_slots에 대해 수행됩니다.
    transformed_slots = {**active_slots}

    # 구매 품의서(`items` 키 사용)의 아이템별 특별 처리:
    # - 납기요청일(`item_delivery_request_date`)을 `item_delivery_date`로 변경 및 파싱.
    # - 사용목적(`item_purpose`)을 `item_notes`로 변경 (기존 `item_notes`가 없는 경우).
    if "items" in transformed_slots and isinstance(transformed_slots["items"], list):
        updated_items = []
        for item in transformed_slots["items"]:
            if isinstance(item, dict):
                processed_item = {**item}  # 원본 수정을 피하기 위해 복사

                # 'item_delivery_request_date'를 'item_delivery_date'로 변환 및 파싱
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
                        # 파싱 실패 시 원본 값 유지 또는 경고 로깅
                        logging.warning(
                            f"Failed to parse item_delivery_request_date: {processed_item['item_delivery_request_date']}. Keeping original if item_delivery_date not present."
                        )
                        if "item_delivery_date" not in processed_item:
                            processed_item["item_delivery_date"] = processed_item[
                                "item_delivery_request_date"
                            ]
                    # 원본 키는 삭제하여 혼동 방지 (단, 값이 실제로 변경되었을 때만)
                    if (
                        "item_delivery_request_date" in processed_item
                        and "item_delivery_date" in processed_item
                        and processed_item["item_delivery_request_date"]
                        != processed_item["item_delivery_date"]
                    ):
                        del processed_item["item_delivery_request_date"]

                # 'item_purpose'를 'item_notes'로 매핑 (기존 'item_notes'가 없거나 비어있을 경우)
                if "item_purpose" in processed_item:
                    if (
                        "item_notes" not in processed_item
                        or not processed_item[
                            "item_notes"
                        ]  # item_notes가 빈 문자열일 경우에도 purpose 사용
                    ):
                        processed_item["item_notes"] = processed_item["item_purpose"]
                        logging.debug(
                            f"Item's 'item_purpose' ('{processed_item['item_purpose']}') mapped to 'item_notes'"
                        )
                        # 원본 키는 삭제 (단, 값이 실제로 복사되었을 때만)
                        if (
                            "item_purpose" in processed_item
                            and "item_notes" in processed_item
                            and processed_item["item_purpose"]
                            == processed_item["item_notes"]
                        ):
                            del processed_item["item_purpose"]
                    elif processed_item["item_purpose"] != processed_item["item_notes"]:
                        # item_notes가 이미 존재하고, item_purpose와 다른 값을 가질 경우, item_purpose는 유지 (혹은 로깅만)
                        logging.debug(
                            f"Item's 'item_purpose' ('{processed_item['item_purpose']}') not mapped to 'item_notes' as 'item_notes' already exists with value: '{processed_item['item_notes']}'"
                        )
                updated_items.append(processed_item)
            else:
                updated_items.append(item)  # 딕셔너리가 아닌 아이템은 그대로 추가
        transformed_slots["items"] = updated_items
        logging.info(
            f"Items list processed for date and purpose mapping: {transformed_slots['items']}"
        )

    # 개인 경비 사용 내역서 (`expense_items` 키 사용)의 아이템별 날짜 처리:
    # - 사용일자(`expense_date`)를 파싱합니다.
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

    # 법인카드 지출내역서 (`card_usage_items` 키 사용)의 아이템별 날짜 처리:
    # - 사용일자(`usage_date`)를 파싱합니다.
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

    # 휴가 종류 텍스트를 HTML <select>의 value로 매핑합니다.
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
            # 매핑되지 않는 경우 원본 값 유지 (HTML에 해당 option이 없을 수 있음)
            logging.warning(
                f"Slot 'leave_type' text '{leave_type_text}' not found in LEAVE_TYPE_TEXT_TO_VALUE_MAP. Keeping original."
            )

    # 야근 시간 오전/오후 구분 값을 "AM" 또는 "PM"으로 표준화합니다.
    if "overtime_ampm" in transformed_slots and isinstance(
        transformed_slots["overtime_ampm"], str
    ):
        ampm_value_original = transformed_slots["overtime_ampm"]
        ampm_value_upper = ampm_value_original.upper()
        if (
            "밤" in ampm_value_original
            or "오후" in ampm_value_original
            or "P" in ampm_value_upper  # PM, P.M. 등 고려
        ):
            transformed_slots["overtime_ampm"] = "PM"
        elif (
            "새벽" in ampm_value_original
            or "오전" in ampm_value_original
            or "A" in ampm_value_upper  # AM, A.M. 등 고려
        ):
            transformed_slots["overtime_ampm"] = "AM"
        # 정확히 매칭되지 않으면 원본 값을 유지 (HTML option에 해당 값이 없을 수 있음)
        logging.debug(
            f"Slot 'overtime_ampm' preprocessed: '{ampm_value_original}' -> '{transformed_slots['overtime_ampm']}'"
        )

    # 일반적인 슬롯 값들에 대한 변환 (날짜, 시간 등)
    for key, value in list(
        transformed_slots.items()
    ):  # list()를 사용하여 반복 중 딕셔너리 변경에 안전하게 처리
        logging.debug(f"Processing slot - Key: {key}, Value: {value}")
        if isinstance(value, str):
            original_value_for_logging = value  # 로깅용 원본 값 저장

            # `leave_type`과 `overtime_ampm`은 위에서 이미 처리되었으므로 건너뜁니다.
            if key == "overtime_ampm" or key == "leave_type":
                continue

            # 회의 시간 관련 슬롯 처리 (`parse_datetime_description_to_iso_local` 사용)
            # 예: "내일 오후 3시", "다음주 월요일 10:00"
            if key == "meeting_datetime" or key == "meeting_time":
                parsed_datetime = parse_datetime_description_to_iso_local(value)
                if parsed_datetime:
                    transformed_slots[key] = parsed_datetime
                    logging.debug(
                        f"Datetime slot '{key}' processed: '{original_value_for_logging}' -> '{transformed_slots[key]}'"
                    )
                # 파싱 실패 시 원본 값 유지 (transformed_slots에는 이미 active_slots의 원본 값이 있음)
                continue  # 다음 슬롯으로 넘어감
            elif (
                key == "meeting_time_description"
            ):  # LLM이 meeting_datetime 대신 이 키로 줄 수도 있음
                parsed_datetime = parse_datetime_description_to_iso_local(value)
                if parsed_datetime:
                    transformed_slots["meeting_datetime"] = (
                        parsed_datetime  # meeting_datetime 키로 통일
                    )
                    # 원래 meeting_time_description 슬롯은 제거하거나, 필요시 유지할 수 있음
                    if key in transformed_slots:  # transformed_slots에 아직 있다면 삭제
                        del transformed_slots[key]
                    logging.debug(
                        f"Datetime slot '{key}' (-> meeting_datetime) processed: '{original_value_for_logging}' -> '{transformed_slots['meeting_datetime']}'"
                    )
                continue

            # 일반적인 날짜 슬롯 처리 (키 이름에 "date", "일자", "기간" 포함 시)
            # `parse_relative_date_to_iso` 사용. 예: "어제", "다음주 금요일"
            key_lower = key.lower()
            is_date_slot = any(
                substring in key_lower for substring in DATE_SLOT_KEY_SUBSTRINGS
            )
            if is_date_slot:
                # 아이템 리스트 내의 날짜 필드는 위에서 이미 처리되었으므로, 여기서는 중복 처리하지 않도록 주의합니다.
                # 현재 로직에서는 아이템 리스트 처리가 이 루프보다 먼저 수행되므로 괜찮습니다.
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
        f"Final slots prepared for template filling after all transformations: {transformed_slots}"
    )

    # JavaScript로 전달될 아이템 리스트용 JSON 문자열 생성 (`items_json_str`).
    # 이 작업은 모든 슬롯 값 변환(특히 날짜 파싱)이 완료된 *후*에 수행되어야 합니다.
    # HTML의 <input type="date"> 필드 등이 올바른 형식의 날짜 값을 받도록 하기 위함입니다.
    items_json_str = "null"  # 기본값
    item_keys_for_js = ["items", "expense_items", "card_usage_items"]

    for item_key in item_keys_for_js:
        if item_key in transformed_slots and isinstance(
            transformed_slots[item_key], list
        ):
            # 모든 변환이 완료된 최종 아이템 리스트를 JSON으로 직렬화합니다.
            final_items_list_for_json = transformed_slots.get(item_key, [])
            items_json_str = json.dumps(final_items_list_for_json, ensure_ascii=False)
            logging.debug(
                f"Slot '{item_key}' (transformed values) will be passed to JS as JSON: {items_json_str}"
            )
            break  # 첫 번째로 발견되는 아이템 리스트만 사용 (일반적으로 양식당 하나만 존재)

    logging.info(
        f"Attempting to fill template. items_json_str (first 200 chars): {items_json_str[:200]}"
    )
    logging.info(f"Template before re.sub (first 300 chars): {template[:300]}")

    # HTML 템플릿의 플레이스홀더를 실제 값으로 치환합니다.
    # replacer 함수는 {key} 또는 {items_json} 형태의 플레이스홀더를 처리합니다.
    def replacer(match):
        key_in_template = match.group(1)  # 매칭된 그룹 (중괄호 안의 내용)

        if key_in_template == "items_json":
            # `items_json_str`은 이미 `json.dumps`를 통해 올바르게 이스케이프된 JSON 문자열입니다.
            # 따라서 추가적인 백슬래시 이스케이프 없이 그대로 반환합니다.
            return items_json_str

        # `transformed_slots`에서 해당 키의 값을 가져옵니다.
        # 값이 없을 경우 빈 문자열로 대체하여 HTML이 깨지지 않도록 합니다.
        value_to_return = transformed_slots.get(key_in_template, "")

        # `re.sub`는 백슬래시를 특별하게 취급하므로, 삽입될 문자열 값에 포함된 백슬래시를 이스케이프 처리합니다.
        # 예를 들어, 슬롯 값이 "C:\path\to\file" 이라면, "C:\\path\\to\\file"로 변경되어야
        # `re.sub`가 이를 올바르게 "C:\path\to\file"로 HTML에 삽입합니다.
        # 숫자나 다른 타입은 문자열로 변환하여 처리합니다.
        if isinstance(value_to_return, str):
            return value_to_return.replace("\\", "\\\\")  # 백슬래시 이스케이프
        else:
            return str(value_to_return)  # 다른 타입은 문자열로 변환

    # 정규식을 사용하여 HTML 템플릿 내의 모든 {플레이스홀더_이름}을 치환합니다.
    # 플레이스홀더 이름은 영문자, 숫자, 언더스코어(_)로 구성될 수 있습니다 (예: {user_name}, {items_json}).
    filled_template = re.sub(r"{(\w+)}", replacer, template)

    logging.info(
        f"Template after re.sub (first 300 chars of filled_template): {filled_template[:300]}"
    )

    return (
        filled_template,
        transformed_slots,  # 최종적으로 UI 등에 전달될, 모든 변환이 완료된 슬롯
    )


def classify_and_extract_slots_for_template(user_input: UserInput) -> Dict[str, Any]:
    """사용자 입력을 기반으로 양식을 분류하고, 슬롯을 추출하여 HTML 템플릿을 채웁니다.

    이 함수는 전체 요청 처리 파이프라인을 담당하며 다음 단계를 포함합니다:
    1.  **양식 분류**: `get_form_classifier_chain`으로 생성된 LLM 체인을 사용하여 사용자 입력으로부터
        양식 유형 (`form_type`)과 검색 키워드 (`keywords`)를 추출합니다.
        -   분류 실패 또는 LLM 출력 파싱 오류(`OutputParserException`) 시, 사용자에게 되묻거나
            오류를 알리는 응답 (`error: "CLASSIFICATION_FAILED"`)을 반환합니다.
        -   기타 예상치 못한 오류 발생 시 `error: "CLASSIFICATION_UNEXPECTED_ERROR"`를 반환합니다.
    2.  **양식 유효성 검사**: 분류된 `form_type`이 `AVAILABLE_FORM_TYPES` (사전에 정의된 지원 양식 목록)에
        포함되어 있는지 확인합니다. 없는 경우 `error: "UNKNOWN_FORM_TYPE_CLASSIFIED"`를 반환합니다.
    3.  **HTML 템플릿 검색**: RAG 시스템 (`retrieve_template`)을 사용하여 분류된 `form_type`과 `keywords`에
        가장 적합한 HTML 템플릿을 검색합니다.
        -   템플릿 검색 실패 시, `error: "TEMPLATE_NOT_FOUND"`를 반환합니다.
    4.  **슬롯 추출**: 해당 `form_type`에 맞는 슬롯 추출기 LLM (`SLOT_EXTRACTOR_CHAINS`에서 가져옴)을 호출하여
        사용자 입력으로부터 상세 슬롯 값들을 추출합니다.
        -   슬롯 추출 모델은 Pydantic 모델 객체를 반환하며, 이를 `.model_dump()`를 통해 딕셔너리로 변환합니다.
        -   **회의비 지출결의서 특별 처리**: `venue_fee`(회의실 대관료), `refreshment_fee`(다과비),
            `llm_expense_details`(기타 상세) 슬롯 값들을 조합하여 `expenses`라는 단일 슬롯으로 만듭니다.
            만약 이들이 없고 `amount`만 있다면, `amount`를 사용하여 `expenses`를 채웁니다.
        -   슬롯 추출 중 `OutputParserException` 발생 시 (LLM 출력이 Pydantic 모델로 파싱 실패 등) 로깅만 하고
            빈 슬롯(`{}`)으로 다음 단계를 진행할 수 있으나, 현재는 특별한 오류 반환 없이 진행됩니다.
            (필요시 오류 응답 추가 가능)
    5.  **슬롯 값 채우기**: `fill_slots_in_template` 함수를 호출하여 검색된 HTML 템플릿에 추출 및 처리된
        슬롯 값들을 채웁니다.
    6.  **결과 반환**: 최종적으로 API 응답에 필요한 모든 정보 (양식 유형, 키워드, 채워진 슬롯, HTML 템플릿 등)를
        포함하는 딕셔너리를 반환합니다.

    Args:
        user_input: 사용자의 원본 입력 문자열을 포함하는 `UserInput` 객체.

    Returns:
        Dict[str, Any]: API 응답으로 사용될 딕셔너리. 주요 키는 다음과 같습니다:
            - "form_type": (str) 분류된 양식 종류 (예: "구매 품의서").
            - "keywords": (List[str]) 추출된 검색 키워드 리스트.
            - "slots": (Dict[str, Any]) 최종적으로 처리되고 HTML에 채워진 슬롯 값 딕셔너리.
            - "html_template": (str) 슬롯 값이 모두 채워진 최종 HTML 문자열.
            - "original_input": (str) 사용자의 원본 입력.
            - "error": (str, optional) 오류 발생 시 오류 코드 (예: "CLASSIFICATION_FAILED").
            - "message_to_user": (str, optional) 오류 발생 시 사용자에게 보여줄 메시지.
            - "available_forms": (List[str], optional) 분류 실패 시 사용 가능한 양식 목록.
    """
    # 1단계: 양식 분류 및 키워드 추출
    form_classifier_chain = get_form_classifier_chain()
    try:
        classifier_result = form_classifier_chain.invoke({"input": user_input.input})
        logging.info(f"Classifier result: {classifier_result}")
        if (
            not classifier_result
            or not hasattr(classifier_result, "form_type")
            or not classifier_result.form_type  # form_type이 비어있거나 None인 경우도 실패로 간주
        ):
            # LLM이 유효한 form_type을 반환하지 못한 경우
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
    except (
        Exception
    ) as e:  # OutputParserException 외의 다른 예외 (API 호출 실패, 네트워크 오류 등)
        logging.error(
            f"Form classification failed with an unexpected error: {e}", exc_info=True
        )
        return {
            "error": "CLASSIFICATION_UNEXPECTED_ERROR",
            "message_to_user": "양식 분류 중 예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "original_input": user_input.input,
        }

    form_type = classifier_result.form_type
    keywords = (
        classifier_result.keywords if hasattr(classifier_result, "keywords") else []
    )

    # 분류된 form_type이 시스템에서 지원하는 양식인지 확인합니다.
    if form_type not in AVAILABLE_FORM_TYPES:
        logging.warning(
            f"Unknown form_type classified: {form_type}. Available: {AVAILABLE_FORM_TYPES}"
        )
        return {
            "error": "UNKNOWN_FORM_TYPE_CLASSIFIED",
            "message_to_user": f"죄송합니다. '{form_type}'은(는) 현재 지원하지 않는 문서 종류입니다. 다음 중에서 선택해 주세요.",
            "available_forms": AVAILABLE_FORM_TYPES,
            "original_input": user_input.input,
            "form_type": form_type,  # 사용자가 어떤 알 수 없는 양식을 요청했는지 알려줌
        }

    # 2단계: HTML 템플릿 검색 (RAG 사용)
    # retrieve_template 함수는 form_type (예: "연차 신청서")과 keywords를 사용하여 적절한 HTML 템플릿 문자열을 반환합니다.
    retrieved_template_html = retrieve_template(form_type=form_type, keywords=keywords)

    if not retrieved_template_html:
        logging.warning(
            f"Template not found for form_type: {form_type} with keywords: {keywords}"
        )
        # RAG를 통해 템플릿을 찾지 못한 경우, 사용자에게 알립니다.
        # TEMPLATE_FILENAME_MAP을 사용하여 파일 시스템에 해당 form_type의 기본 템플릿이 존재하는지 확인하는
        # 추가적인 방어 로직을 넣을 수도 있지만, 현재는 retrieve_template 실패 시 바로 오류로 처리합니다.
        return {
            "error": "TEMPLATE_NOT_FOUND",
            "message_to_user": f"'{form_type}' 양식의 내용을 찾을 수 없습니다. 검색어를 변경하거나 관리자에게 문의해주세요.",
            "form_type": form_type,
            "keywords": keywords,
            "original_input": user_input.input,
            "available_forms": AVAILABLE_FORM_TYPES,
        }
    logging.info(f"Retrieved template for form_type: {form_type}")

    # 3단계: 양식별 슬롯 추출
    raw_slots: Dict[str, Any] = (
        {}
    )  # LLM이 추출한 원본 슬롯 (Pydantic 모델 객체에서 변환된 dict)
    if form_type in SLOT_EXTRACTOR_CHAINS:
        slot_chain = SLOT_EXTRACTOR_CHAINS[form_type]
        try:
            # 슬롯 추출 LLM은 Pydantic 모델 객체를 반환합니다.
            extracted_slots_model = slot_chain.invoke({"input": user_input.input})
            logging.info(
                f"Extracted slots model for {form_type}: {extracted_slots_model}"
            )
            if extracted_slots_model:
                # Pydantic 모델을 딕셔너리로 변환합니다.
                # .model_dump()는 Pydantic V2 스타일이며, V1에서는 .dict()를 사용합니다.
                # 현재 프로젝트의 schema.py가 langchain_core.pydantic_v1을 사용하고 있으므로,
                # .dict() 또는 .model_dump() (호환성 shim이 있다면)가 적절합니다.
                # 여기서는 .model_dump()가 일반적으로 더 권장되므로 사용합니다.
                raw_slots = extracted_slots_model.model_dump()

                # --- "회의비 지출결의서" 특별 처리 로직 ---
                # venue_fee(장소 대관료), refreshment_fee(다과비), llm_expense_details(기타 상세)를 조합하여
                # expenses(지출 내역 상세) 슬롯을 생성합니다.
                if form_type == "회의비 지출결의서":
                    expense_details_parts = []
                    venue_fee = raw_slots.get("venue_fee")
                    refreshment_fee = raw_slots.get("refreshment_fee")
                    llm_expense_details = raw_slots.get(
                        "expense_details"
                    )  # LLM이 직접 추출한 상세내역

                    if venue_fee:
                        expense_details_parts.append(f"회의실 대관료: {venue_fee}")
                    if refreshment_fee:
                        expense_details_parts.append(f"다과비: {refreshment_fee}")

                    # LLM이 추출한 expense_details가 있다면 추가합니다.
                    if llm_expense_details:
                        # venue_fee나 refreshment_fee가 이미 있는 경우, "기타 상세:" 프리픽스를 붙여 구분합니다.
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
                        # 장소, 다과, 기타 상세는 없지만 총액(amount)만 있는 경우, 이를 사용해 expenses를 채웁니다.
                        raw_slots["expenses"] = f"총 지출: {raw_slots.get('amount')}"
                        logging.info(
                            f"Using total amount for 'expenses': {raw_slots['expenses']}"
                        )
                    # 기존 venue_fee, refreshment_fee, expense_details는 필요에 따라 삭제하거나 유지할 수 있습니다.
                    # 현재는 expenses로 조합되었으므로, 중복을 피하기 위해 삭제하는 것을 고려할 수 있습니다.
                    # for key_to_del in ["venue_fee", "refreshment_fee", "expense_details"]:
                    #     if key_to_del in raw_slots: del raw_slots[key_to_del]
            else:
                # LLM이 슬롯 추출 결과로 None을 반환한 경우 (예: 입력에서 정보를 찾을 수 없음)
                logging.warning(
                    f"Slot extraction returned None for {form_type}. Proceeding with empty slots."
                )
                raw_slots = {}  # 빈 딕셔너리로 초기화
        except OutputParserException as e:
            # LLM의 출력이 Pydantic 모델로 파싱되지 않는 경우
            logging.error(
                f"Slot extraction parsing failed for {form_type}: {e}. Proceeding with empty slots for this form."
            )
            raw_slots = (
                {}
            )  # 파싱 실패 시 빈 슬롯으로 처리하여, 템플릿은 보여주되 내용은 비어있게 함
        except Exception as e:
            # 슬롯 추출 중 기타 예상치 못한 오류 발생 시
            logging.error(
                f"Slot extraction failed with an unexpected error for {form_type}: {e}",
                exc_info=True,
            )
            # 이 경우에도 일단 빈 슬롯으로 진행하거나, 또는 에러 응답을 반환할 수 있습니다.
            # 현재는 빈 슬롯으로 진행하여 템플릿이라도 보여주도록 합니다.
            raw_slots = {}
    else:
        # 해당 양식에 대한 슬롯 추출기 자체가 정의되지 않은 경우 (FORM_CONFIGS에 없음)
        logging.warning(
            f"No slot extractor chain found for form_type: {form_type}. Proceeding without slot extraction."
        )
        raw_slots = {}

    # 4단계: 슬롯 값 변환 및 HTML 템플릿 채우기
    # fill_slots_in_template 함수는 raw_slots에 있는 값들을 기반으로 날짜 변환, 키 변경 등을 수행하고,
    # 최종적으로 HTML 템플릿에 값들을 채워넣습니다.
    final_html, final_processed_slots = fill_slots_in_template(
        retrieved_template_html, raw_slots
    )
    logging.info(
        f"Final processed slots after fill_slots_in_template: {final_processed_slots}"
    )
    # logging.info(f"Final HTML template (first 500 chars): {final_html[:500]}...") # 너무 길면 일부만 로깅

    # 5단계: 최종 결과 반환
    return {
        "form_type": form_type,
        "keywords": keywords,
        "slots": final_processed_slots,  # 최종적으로 변환되고 HTML에 채워진 슬롯
        "html_template": final_html,  # 슬롯 값이 모두 채워진 HTML 문자열
        "original_input": user_input.input,  # 사용자의 원본 입력
        # 오류 발생 시에는 "error", "message_to_user" 등이 이전에 반환되었을 것임
    }


# 기존 classify_and_get_template 함수는 classify_and_extract_slots_for_template로 대체되었으므로 주석 처리 또는 삭제 가능.
# def classify_and_get_template(user_input: UserInput) -> Dict[str, Any]:
#     ...
