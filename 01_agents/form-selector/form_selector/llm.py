import os
from dotenv import load_dotenv
import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage

# OutputFixingParser는 필요에 따라 각 체인에 선택적으로 적용하거나, 초기에는 제외하고 테스트 후 추가 고려
# from langchain.output_parsers import OutputFixingParser

# schema.py에서 새로운 Pydantic 모델들을 가져옵니다.
from .schema import (
    FormClassifierOutput,
    AnnualLeaveSlots,
    BusinessTripSlots,
    MeetingExpenseSlots,
    OtherExpenseSlots,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)

# 사용 가능한 양식 타입 - RAG 검색 및 슬롯 추출기 선택에 사용될 수 있음
AVAILABLE_FORM_TYPES = [
    "연차 신청서",
    "출장비 신청서",
    "회의비 지출결의서",
    "기타 비용 청구서",
]

# 기본 LLM 모델 (모든 체인에서 공유 가능)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")


# _create_prompt_from_file 함수는 이제 직접 사용되지 않음 (필요시 삭제)
# def _create_prompt_from_file(filename: str) -> ChatPromptTemplate:
#     """프롬프트 파일로부터 ChatPromptTemplate 객체를 생성합니다."""
#     file_path = os.path.join(PROMPT_DIR, filename)
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(f"Prompt file not found: {file_path}")
#     return ChatPromptTemplate.from_template(
#         open(file_path, "r", encoding="utf-8").read()
#     )


# --- 1단계: 양식 분류 체인 ---
def get_form_classifier_chain():
    """사용자 입력으로부터 양식 종류와 키워드를 추출하는 LCEL 체인을 반환합니다."""
    parser = PydanticOutputParser(pydantic_object=FormClassifierOutput)

    prompt_filename = "form_classifier_prompt.txt"
    prompt_content_template = open(
        os.path.join(PROMPT_DIR, prompt_filename), "r", encoding="utf-8"
    ).read()

    # 프롬프트 파일 형식: SYSTEM: ... HUMAN: {input} ASSISTANT:
    # 여기서 SYSTEM 부분만 추출하고, HUMAN, ASSISTANT는 from_messages에서 직접 정의
    # ASSISTANT: 부분도 LLM 출력을 유도하는데 사용될 수 있으므로, 필요시 포함하여 split 기준 변경
    parts = prompt_content_template.split("HUMAN:")
    system_message_content_template = parts[0].replace("SYSTEM:", "").strip()
    # human_template_part = parts[1].split("ASSISTANT:")[0].strip() # 여기서는 {input}을 직접 사용
    # ai_start_part = parts[1].split("ASSISTANT:")[1].strip() if len(parts) > 1 and "ASSISTANT:" in parts[1] else ""

    system_message_content_with_instructions = system_message_content_template.replace(
        "{format_instructions}", parser.get_format_instructions()
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content_with_instructions),
            ("human", "{input}"),
            # ("ai", ai_start_part if ai_start_part else "```json") # 프롬프트 파일의 ASSISTANT: 이후 내용을 사용하거나 기본값 사용
        ]
    )

    return prompt | llm | parser


# --- 2단계: 양식별 슬롯 추출 체인 ---


def _create_slot_extraction_chain(prompt_filename: str, pydantic_schema_class):
    parser = PydanticOutputParser(pydantic_object=pydantic_schema_class)

    prompt_content_template = open(
        os.path.join(PROMPT_DIR, prompt_filename), "r", encoding="utf-8"
    ).read()

    parts = prompt_content_template.split("HUMAN:")
    system_message_content_template = parts[0].replace("SYSTEM:", "").strip()
    # human_template_part = parts[1].split("ASSISTANT:")[0].strip()
    # ai_start_part = parts[1].split("ASSISTANT:")[1].strip() if len(parts) > 1 and "ASSISTANT:" in parts[1] else ""

    system_message_content_with_instructions = system_message_content_template.replace(
        "{format_instructions}", parser.get_format_instructions()
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content_with_instructions),
            ("human", "{input}"),
            # ("ai", ai_start_part if ai_start_part else "```json")
        ]
    )

    return prompt | llm | parser


# service.py에서 사용할 슬롯 추출 체인 맵
SLOT_EXTRACTOR_CHAINS = {
    "연차 신청서": _create_slot_extraction_chain(
        "annual_leave_slots_prompt.txt", AnnualLeaveSlots
    ),
    "출장비 신청서": _create_slot_extraction_chain(
        "business_trip_slots_prompt.txt", BusinessTripSlots
    ),
    "회의비 지출결의서": _create_slot_extraction_chain(
        "meeting_expense_slots_prompt.txt", MeetingExpenseSlots
    ),
    "기타 비용 청구서": _create_slot_extraction_chain(
        "other_expense_slots_prompt.txt", OtherExpenseSlots
    ),
}

if __name__ == "__main__":
    # 간단한 테스트 로직 (실제 운영에서는 service.py를 통해 호출)

    # 1단계 테스트
    classifier_chain = get_form_classifier_chain()
    test_input_text = (
        "다음 주 월요일부터 3일간 연차 쓰고 싶어요. 사유는 개인 건강 문제입니다."
    )
    try:
        classification_result = classifier_chain.invoke({"input": test_input_text})
        logging.info(f"Classification Result: {classification_result}")

        # 2단계 테스트 (분류 결과에 따라)
        if (
            classification_result
            and hasattr(classification_result, "form_type")
            and classification_result.form_type in SLOT_EXTRACTOR_CHAINS
        ):
            form_type = classification_result.form_type
            slot_chain = SLOT_EXTRACTOR_CHAINS[form_type]
            slots_result = slot_chain.invoke(
                {"input": test_input_text}
            )  # 원본 입력을 다시 사용
            logging.info(f"Slots for '{form_type}': {slots_result}")

            # MeetingExpenseSlots 테스트 (meeting_datetime 확인용)
            test_meeting_input = "오늘 오후 3시에 마케팅팀 주간 회의가 있었는데, 회의실 대관료 5만원이랑 다과비 2만원 썼어요."
            meeting_classifier_result = classifier_chain.invoke(
                {"input": test_meeting_input}
            )
            if (
                meeting_classifier_result
                and hasattr(meeting_classifier_result, "form_type")
                and meeting_classifier_result.form_type == "회의비 지출결의서"
            ):
                meeting_slot_chain = SLOT_EXTRACTOR_CHAINS["회의비 지출결의서"]
                meeting_slots_result = meeting_slot_chain.invoke(
                    {"input": test_meeting_input}
                )
                logging.info(f"Slots for '회의비 지출결의서': {meeting_slots_result}")
                if meeting_slots_result and hasattr(
                    meeting_slots_result, "meeting_datetime"
                ):
                    logging.info(
                        f"Extracted meeting_datetime: {meeting_slots_result.meeting_datetime}"
                    )

        else:
            logging.warning(
                "Form type not found in SLOT_EXTRACTOR_CHAINS or classification failed."
            )
            if classification_result and not hasattr(
                classification_result, "form_type"
            ):
                logging.warning(
                    f"Classification result object does not have 'form_type' attribute. Result: {classification_result}"
                )

    except Exception as e:
        logging.error(f"Error during llm.py test: {e}", exc_info=True)
