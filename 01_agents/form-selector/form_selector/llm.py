import os
from dotenv import load_dotenv
import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import SystemMessage
from langchain.output_parsers import PydanticOutputParser

# schema.py에서 FormClassifierOutput만 가져오고, 각 슬롯 모델은 form_configs.py를 통해 간접적으로 사용
from .schema import FormClassifierOutput

# form_configs.py에서 양식 설정과 관련된 정보들을 가져옴
from .form_configs import FORM_CONFIGS, AVAILABLE_FORM_TYPES

load_dotenv()
logging.basicConfig(level=logging.INFO)

# 기본 LLM 모델 (모든 체인에서 공유 가능)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# PROMPT_DIR 상수를 정의할 필요가 없어짐. form_configs.py에서 이미 상대 경로를 포함한 파일명을 제공.
# PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")


# --- 1단계: 양식 분류 체인 ---
def get_form_classifier_chain():
    """사용자 입력으로부터 양식 종류와 키워드를 추출하는 LCEL 체인을 반환합니다."""
    parser = PydanticOutputParser(pydantic_object=FormClassifierOutput)

    # form_classifier_prompt.txt는 위치가 고정적이므로, 이 부분은 현재 경로 기준으로 처리
    classifier_prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "form_classifier_prompt.txt"
    )
    prompt_content_template = open(classifier_prompt_path, "r", encoding="utf-8").read()

    system_message_content_with_instructions = prompt_content_template.replace(
        "{format_instructions}", parser.get_format_instructions()
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content_with_instructions),
            ("human", "{input}"),
        ]
    )
    return prompt | llm | parser


# --- 2단계: 양식별 슬롯 추출 체인 --- (FORM_CONFIGS를 사용하여 동적 생성)
def _create_slot_extraction_chain(form_config_prompt_path: str, pydantic_schema_class):
    parser = PydanticOutputParser(pydantic_object=pydantic_schema_class)

    # form_configs.py에서 제공하는 prompt_template_path는 이 파일(llm.py) 기준의 상대 경로임.
    # 예를 들어 "prompts/annual_leave_slots_prompt.txt"
    # os.path.join(os.path.dirname(__file__), form_config_prompt_path) 를 사용하면
    # .../form_selector/form_selector/ + prompts/annual_leave_slots_prompt.txt 가 되어 올바른 경로가 됨.
    absolute_prompt_path = os.path.join(
        os.path.dirname(__file__), form_config_prompt_path
    )

    prompt_content_template = open(absolute_prompt_path, "r", encoding="utf-8").read()

    system_message_content_with_instructions = prompt_content_template.replace(
        "{format_instructions}", parser.get_format_instructions()
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content_with_instructions),
            ("human", "{input}"),
        ]
    )
    return prompt | llm | parser


# service.py에서 사용할 슬롯 추출 체인 맵 (동적 생성)
SLOT_EXTRACTOR_CHAINS = {
    form_name: _create_slot_extraction_chain(config.prompt_template_path, config.model)
    for form_name, config in FORM_CONFIGS.items()
}

if __name__ == "__main__":
    # 간단한 테스트 로직 (실제 운영에서는 service.py를 통해 호출)
    logging.info(f"사용 가능한 양식: {AVAILABLE_FORM_TYPES}")
    logging.info(f"슬롯 추출기 설정된 양식: {list(SLOT_EXTRACTOR_CHAINS.keys())}")

    # 1단계 테스트
    classifier_chain = get_form_classifier_chain()
    test_input_text = (
        "다음 주 월요일부터 3일간 연차 쓰고 싶어요. 사유는 개인 건강 문제입니다."
    )
    try:
        classification_result = classifier_chain.invoke({"input": test_input_text})
        logging.info(f"분류 결과: {classification_result}")

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
            logging.info(f"'{form_type}' 슬롯 추출 결과: {slots_result}")

        # 야근식대비용 신청서 테스트
        dinner_test_input = "개발팀 홍길동입니다. 어제 야근 식대 신청합니다. 제목은 '11월 25일 야근식대 신청'. 사번은 2023001, 직위는 선임, 연락처 010-1234-5678. 업무 내용은 긴급 버그 수정이었고, 야근 장소는 회사입니다. 어제 밤 10시 30분까지 일했고, 식대로 12000원 썼습니다. 신청은 오늘 날짜로 하고, 입금은 우리은행 123-456-789 홍길동으로 해주세요."
        dinner_classification_result = classifier_chain.invoke(
            {"input": dinner_test_input}
        )
        logging.info(f"야근식대 분류 결과: {dinner_classification_result}")
        if (
            dinner_classification_result
            and hasattr(dinner_classification_result, "form_type")
            and dinner_classification_result.form_type == "야근식대비용 신청서"
            and dinner_classification_result.form_type in SLOT_EXTRACTOR_CHAINS
        ):
            dinner_slot_chain = SLOT_EXTRACTOR_CHAINS["야근식대비용 신청서"]
            dinner_slots_result = dinner_slot_chain.invoke({"input": dinner_test_input})
            logging.info(f"야근식대 슬롯 추출 결과: {dinner_slots_result}")

    except Exception as e:
        logging.error(f"llm.py 테스트 중 오류 발생: {e}", exc_info=True)
