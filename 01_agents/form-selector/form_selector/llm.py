"""
LangChain을 사용하여 LLM(Large Language Model) 체인을 구성하고 관리하는 모듈입니다.

이 모듈은 전자결재 시스템의 핵심적인 두 가지 LLM 기반 기능을 담당합니다:
1.  **양식 분류 (Form Classification)**:
    사용자의 자연어 입력으로부터 어떤 종류의 전자결재 양식을 요청하는지 식별하고,
    관련 검색 키워드를 추출합니다. (`get_form_classifier_chain`)
2.  **슬롯 추출 (Slot Extraction)**:
    분류된 특정 양식에 필요한 구체적인 정보(슬롯 값)들을 사용자 입력에서
    추출합니다. 각 양식마다 별도의 슬롯 추출 체인이 동적으로 생성됩니다.
    (`_create_slot_extraction_chain`, `SLOT_EXTRACTOR_CHAINS`)

주요 구성 요소:
-   `ChatOpenAI`: OpenAI의 LLM 모델 (예: "gpt-4o")을 사용합니다.
-   `ChatPromptTemplate`: LLM에 전달될 프롬프트를 구성합니다.
-   `PydanticOutputParser`: LLM의 출력을 사전에 정의된 Pydantic 모델 스키마에 따라
    구조화된 객체로 파싱합니다.
-   `FORM_CONFIGS` (from `.form_configs`): 각 양식별 설정(프롬프트 파일 경로, Pydantic 모델 등)을
    중앙에서 관리하는 설정을 참조합니다.
-   프롬프트 파일: `prompts` 디렉토리에 각 체인 (양식 분류, 슬롯 추출)을 위한 프롬프트 템플릿이 저장되어 있습니다.
"""

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
logger = logging.getLogger(__name__)

# 기본 LLM 모델 (모든 체인에서 공유 가능)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# PROMPT_BASE_DIR: 프롬프트 파일들이 위치한 기본 디렉토리 경로.
# __file__은 현재 파일(llm.py)의 경로를 나타냅니다.
PROMPT_BASE_DIR = os.path.join(os.path.dirname(__file__), "prompts")


# --- 1단계: 양식 분류 체인 ---
def get_form_classifier_chain():
    """사용자 입력으로부터 양식 종류와 키워드를 추출하는 Langchain Expression Language (LCEL) 체인을 생성하여 반환합니다.

    이 체인은 다음 구성 요소로 이루어집니다:
    1. SystemMessage: LLM에게 역할을 부여하고, 출력 형식(JSON)과 사용 가능한 양식 목록을 안내합니다.
       출력 형식은 `FormClassifierOutput` Pydantic 모델을 기반으로 PydanticOutputParser를 통해 주입됩니다.
    2. HumanMessage: 실제 사용자 입력을 받습니다.
    3. ChatOpenAI LLM: 프롬프트를 기반으로 사용자 입력을 처리합니다.
    4. PydanticOutputParser: LLM의 출력을 `FormClassifierOutput` Pydantic 모델 객체로 파싱합니다.

    반환 값:
        LCEL Chain: "input" 문자열을 받아 `FormClassifierOutput` 객체를 반환하는 실행 가능한 체인.
    """
    parser = PydanticOutputParser(pydantic_object=FormClassifierOutput)

    classifier_prompt_filename = (
        "form_classifier_prompt.txt"  # 양식 분류기용 프롬프트 파일명
    )
    classifier_prompt_path = os.path.join(PROMPT_BASE_DIR, classifier_prompt_filename)

    try:
        with open(classifier_prompt_path, "r", encoding="utf-8") as f:
            prompt_content_template = f.read()
    except FileNotFoundError:
        logger.error(
            f"양식 분류 프롬프트 파일을 찾을 수 없습니다: {classifier_prompt_path}"
        )
        raise

    # 프롬프트 템플릿에 Pydantic 파서의 포맷 지침을 주입합니다.
    system_message_content_with_instructions = prompt_content_template.replace(
        "{format_instructions}", parser.get_format_instructions()
    ).replace(
        "{available_forms}",
        ", ".join(AVAILABLE_FORM_TYPES),  # 사용 가능한 양식 목록 주입
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content_with_instructions),
            ("human", "{input}"),  # 사용자 입력 플레이스홀더
        ]
    )

    logger.info("양식 분류 체인이 성공적으로 생성되었습니다.")
    return prompt | llm | parser


# --- 2단계: 양식별 슬롯 추출 체인 --- (FORM_CONFIGS를 사용하여 동적 생성)
def _create_slot_extraction_chain(
    form_name: str, form_config_prompt_filename: str, pydantic_schema_class
):
    """특정 양식의 슬롯을 추출하기 위한 LCEL 체인을 생성합니다. (내부 헬퍼 함수)

    이 함수는 `FORM_CONFIGS`에 정의된 각 양식 설정을 기반으로 호출됩니다.

    Args:
        form_name (str): 현재 처리 중인 양식의 이름 (로깅용).
        form_config_prompt_filename (str): 해당 양식의 슬롯 추출 프롬프트 파일 이름 (예: "annual_leave_slots_prompt.txt").
                                        `PROMPT_BASE_DIR` 기준으로 상대 경로입니다.
        pydantic_schema_class: LLM의 출력을 파싱하는 데 사용될 Pydantic 모델 클래스 (예: AnnualLeaveSlots).

    Returns:
        LCEL Chain: "input" 문자열을 받아 해당 Pydantic 모델 객체를 반환하는 실행 가능한 체인.

    Raises:
        FileNotFoundError: 프롬프트 파일을 찾을 수 없는 경우 발생합니다.
    """
    parser = PydanticOutputParser(pydantic_object=pydantic_schema_class)

    # 프롬프트 파일의 절대 경로 구성
    absolute_prompt_path = os.path.join(PROMPT_BASE_DIR, form_config_prompt_filename)

    try:
        with open(absolute_prompt_path, "r", encoding="utf-8") as f:
            prompt_content_template = f.read()
    except FileNotFoundError:
        logger.error(
            f"'{form_name}' 양식의 슬롯 추출 프롬프트 파일을 찾을 수 없습니다: {absolute_prompt_path}"
        )
        raise

    system_message_content_with_instructions = prompt_content_template.replace(
        "{format_instructions}", parser.get_format_instructions()
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_message_content_with_instructions),
            ("human", "{input}"),
        ]
    )
    logger.debug(f"'{form_name}' 양식 슬롯 추출 체인 생성 완료.")
    return prompt | llm | parser


# service.py에서 사용할 슬롯 추출 체인 맵 (동적 생성)
SLOT_EXTRACTOR_CHAINS = {
    form_name: _create_slot_extraction_chain(
        form_name,  # 로깅을 위해 form_name 전달
        config.prompt_template_path,  # 이제 파일명만 전달 -> prompt_template_path 로 수정
        config.model,
    )
    for form_name, config in FORM_CONFIGS.items()
}
logger.info(
    f"총 {len(SLOT_EXTRACTOR_CHAINS)}개의 양식에 대한 슬롯 추출 체인이 생성되었습니다."
)

if __name__ == "__main__":
    # 이 모듈의 체인들을 테스트하기 위한 간단한 실행 블록입니다.
    # 실제 애플리케이션에서는 `service.py`를 통해 이러한 체인들이 호출됩니다.
    logger.info("--- llm.py 직접 실행 테스트 시작 ---")
    logger.info(f"사용 가능한 양식 (form_configs.py): {AVAILABLE_FORM_TYPES}")
    logger.info(
        f"슬롯 추출기가 설정된 양식 (FORM_CONFIGS 키): {list(SLOT_EXTRACTOR_CHAINS.keys())}"
    )

    # 1단계: 양식 분류 체인 테스트
    classifier_chain = get_form_classifier_chain()
    test_input_text_leave = (
        "다음 주 월요일부터 3일간 연차 쓰고 싶어요. 사유는 개인 건강 문제입니다."
    )
    try:
        logger.info(f"\n[테스트 1] 양식 분류 테스트 입력: '{test_input_text_leave}'")
        classification_result = classifier_chain.invoke(
            {"input": test_input_text_leave}
        )
        logger.info(f"분류 결과: {classification_result}")

        # 2단계: 슬롯 추출 체인 테스트 (분류 결과 기반)
        if (
            classification_result
            and hasattr(classification_result, "form_type")
            and classification_result.form_type in SLOT_EXTRACTOR_CHAINS
        ):
            form_type = classification_result.form_type
            logger.info(
                f"\n[테스트 2] '{form_type}' 슬롯 추출 테스트 입력: '{test_input_text_leave}'"
            )
            slot_chain = SLOT_EXTRACTOR_CHAINS[form_type]
            slots_result = slot_chain.invoke({"input": test_input_text_leave})
            logger.info(f"'{form_type}' 슬롯 추출 결과: {slots_result}")
        else:
            logger.warning("분류된 양식에 대한 슬롯 추출기를 찾을 수 없거나 분류 실패.")

        # 다른 양식 테스트 (예: 야근식대비용 신청서)
        test_input_dinner = "개발팀 홍길동입니다. 어제 야근 식대 신청합니다. 제목은 '11월 25일 야근식대 신청'. 사번은 2023001, 직위는 선임, 연락처 010-1234-5678. 업무 내용은 긴급 버그 수정이었고, 야근 장소는 회사입니다. 어제 밤 10시 30분까지 일했고, 식대로 12000원 썼습니다. 신청은 오늘 날짜로 하고, 입금은 우리은행 123-456-789 홍길동으로 해주세요."
        logger.info(
            f"\n[테스트 3] 야근식대비용 신청서 분류 테스트 입력: '{test_input_dinner[:50]}...'"
        )
        dinner_classification_result = classifier_chain.invoke(
            {"input": test_input_dinner}
        )
        logger.info(f"야근식대 분류 결과: {dinner_classification_result}")

        if (
            dinner_classification_result
            and hasattr(dinner_classification_result, "form_type")
            and dinner_classification_result.form_type
            in SLOT_EXTRACTOR_CHAINS  # "야근식대비용 신청서" 대신 동적으로 확인
        ):
            dinner_form_type = dinner_classification_result.form_type
            logger.info(
                f"\n[테스트 4] '{dinner_form_type}' 슬롯 추출 테스트 입력: '{test_input_dinner[:50]}...'"
            )
            dinner_slot_chain = SLOT_EXTRACTOR_CHAINS[dinner_form_type]
            dinner_slots_result = dinner_slot_chain.invoke({"input": test_input_dinner})
            logger.info(f"'{dinner_form_type}' 슬롯 추출 결과: {dinner_slots_result}")
        else:
            logger.warning("야근식대 분류 실패 또는 슬롯 추출기 없음.")

    except Exception as e:
        logger.error(f"llm.py 테스트 중 오류 발생: {e}", exc_info=True)
    logger.info("--- llm.py 직접 실행 테스트 종료 ---")
