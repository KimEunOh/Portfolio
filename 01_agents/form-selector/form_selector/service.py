# LLM 호출 및 템플릿 반환 서비스 함수 정의 예정

from .llm import get_intent_chain, AVAILABLE_FORM_TYPES
from .schema import UserInput, FormSelectorOutput

# from .template_map import load_template # 기존 template_map 의존성 제거 또는 주석 처리
from .rag import retrieve_template  # RAG 모듈의 retrieve_template 함수 임포트
import re
from langchain_core.exceptions import OutputParserException


def fill_slots_in_template(template: str, slots: dict) -> str:
    if not slots:
        return template

    # {slot명} 형태를 slots 값으로 치환
    def replacer(match):
        key = match.group(1)
        return slots.get(key, match.group(0))

    return re.sub(r"\{(\w+)\}", replacer, template)


def classify_and_get_template(user_input: UserInput):
    chain = get_intent_chain()
    llm_result: FormSelectorOutput = None

    try:
        llm_result = chain.invoke({"input": user_input.input})
    except OutputParserException as e:
        # OutputFixingParser가 최종적으로 파싱에 실패한 경우
        print(f"OutputParserException after retries: {e}")
        return {
            "error": "PARSING_FAILED_ASK_USER",
            "message_to_user": "죄송합니다, 요청하신 내용을 정확히 이해하지 못했습니다. 어떤 종류의 결재 문서를 찾으시나요?",
            "available_forms": AVAILABLE_FORM_TYPES,
            "original_input": user_input.input,
        }

    # LLM 결과가 정상적으로 파싱된 경우 (llm_result가 None이 아님)
    if llm_result:
        retrieved_template_html = retrieve_template(
            query=f"{llm_result.form_type} {' '.join(llm_result.keywords)}",
            form_type_hint=llm_result.form_type,
        )

        if not retrieved_template_html:
            # RAG 검색 실패 또는 LLM이 이상한 form_type 반환
            return {
                "error": "TEMPLATE_NOT_FOUND",
                "message_to_user": f"'{llm_result.form_type}' 양식을 찾을 수 없습니다. 다른 양식을 선택하거나 요청을 더 자세히 작성해주세요.",
                "form_type": llm_result.form_type,
                "keywords": llm_result.keywords,
                "slots": llm_result.slots,
                "original_input": user_input.input,
                "available_forms": AVAILABLE_FORM_TYPES,
            }

        final_html = fill_slots_in_template(retrieved_template_html, llm_result.slots)

        return {
            "form_type": llm_result.form_type,
            "keywords": llm_result.keywords,
            "slots": llm_result.slots,
            "html_template": final_html,
            "original_input": user_input.input,
        }
    else:
        # llm_result가 None인 경우는 try 블록에서 예외가 발생하지 않았지만,
        # 어떤 이유로든 결과가 할당되지 않은 극히 예외적인 상황 (이론상 발생하기 어려움)
        # 또는 OutputParserException 외 다른 예외를 여기서 잡아서 처리하고 싶을 때.
        # 여기서는 일반적인 서버 오류로 간주하고 main.py에서 처리되도록 함.
        # 실제로는 이런 경우가 없도록 try-except 구조를 명확히 하는 것이 좋음.
        # 이 예제에서는 OutputParserException만 service에서 특별히 처리하고, 나머지는 main으로 넘김.
        # 따라서 이 else 블록은 사실상 도달하기 어려움.
        return {
            "error": "UNEXPECTED_PROCESSING_ERROR",
            "message_to_user": "요청 처리 중 예기치 않은 오류가 발생했습니다.",
            "original_input": user_input.input,
        }
