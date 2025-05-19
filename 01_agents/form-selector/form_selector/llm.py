# LLM 프롬프트, 체인, OutputParser 관련 함수 및 객체 정의 예정

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from .schema import FormSelectorOutput
import os
from dotenv import load_dotenv

load_dotenv()

# 사용 가능한 양식 종류 정의 (프롬프트와 일치)
AVAILABLE_FORM_TYPES = [
    "연차 신청서",
    "출장비 신청서",
    "회의비 지출결의서",
    "기타 비용 청구서",
]

# LLM 준비 (OPENAI_API_KEY 필요)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 원본 PydanticOutputParser
pydantic_parser = PydanticOutputParser(pydantic_object=FormSelectorOutput)

# OutputFixingParser 생성
# retry 매개변수로 재시도 횟수 지정 가능 (기본값 1)
output_parser = OutputFixingParser.from_llm(
    llm=llm, parser=pydantic_parser, max_retries=3
)  # 최대 3번 재시도

# --- 프롬프트 템플릿 파일에서 로드 --- #
PROMPT_DIR = os.path.dirname(__file__)  # 현재 llm.py 파일이 있는 디렉토리
PROMPT_TEMPLATE_PATH = os.path.join(
    PROMPT_DIR, "prompts", "form_selector_system_prompt.txt"
)

if not os.path.exists(PROMPT_TEMPLATE_PATH):
    raise FileNotFoundError(
        f"프롬프트 템플릿 파일을 찾을 수 없습니다: {PROMPT_TEMPLATE_PATH}"
    )

with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
    prompt_template_str = f.read()
# --- 프롬프트 템플릿 파일에서 로드 완료 --- #

prompt = ChatPromptTemplate.from_template(
    template=prompt_template_str,
    # OutputFixingParser를 사용하므로, 원래 Pydantic parser의 지시사항을 사용
    partial_variables={
        "format_instructions": pydantic_parser.get_format_instructions()
    },
)


def get_intent_chain():
    """LLM intent classifier 체인 반환"""
    # 최종 파서는 OutputFixingParser 인스턴스
    return prompt | llm | output_parser
