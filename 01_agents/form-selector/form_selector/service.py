"""
전자결재 양식 추천 및 슬롯 자동 채우기를 위한 서비스 모듈입니다.

이 모듈은 다음의 주요 기능을 수행합니다:
- 사용자 입력을 받아 적절한 전자결재 양식을 분류합니다.
- 분류된 양식에 필요한 정보를 사용자 입력으로부터 추출(슬롯 필링)합니다.
- 추출된 정보를 HTML 템플릿에 채워 사용자에게 제공합니다.
- 리팩토링된 모듈 구조(processors/, converters/, validators/)를 사용합니다.
"""

# LLM 호출 및 템플릿 반환 서비스 함수 정의 예정
import logging  # 로깅 추가
from typing import Tuple, Dict, Any, Optional
import json  # json 모듈 추가
from datetime import datetime, timedelta  # datetime 추가
import httpx  # httpx 임포트
import os  # 환경 변수 사용을 위해 os 임포트
from . import schema  # schema import 경로 수정 (service.py 기준)

# 새로운 모듈 구조 임포트
from .processors import get_form_processor

# llm.py에서 체인 생성 함수와 SLOT_EXTRACTOR_CHAINS를 가져옴
from .llm import get_form_classifier_chain, SLOT_EXTRACTOR_CHAINS

# form_configs.py에서 사용 가능한 양식 타입 리스트를 가져옴
from .form_configs import AVAILABLE_FORM_TYPES, TEMPLATE_FILENAME_MAP, FORM_CONFIGS

from .utils import (
    parse_relative_date_to_iso,
    parse_datetime_description_to_iso_local,
    parse_date_range_with_context,
)  # utils 모듈에서 함수 임포트
from .rag import retrieve_template  # RAG 모듈의 retrieve_template 함수 임포트
import re
from langchain_core.exceptions import OutputParserException

# 🆕 logger 추가
logger = logging.getLogger(__name__)

# ProcessorFactory import 추가
from .processors.processor_factory import ProcessorFactory


def fill_slots_in_template(
    template: str,
    slots_dict: Dict[str, Any],
    current_date_iso: str,
    form_type: str = "",
) -> Tuple[str, Dict[str, Any]]:
    """새로운 모듈 구조를 사용한 슬롯 처리 함수

    기존 거대한 함수를 리팩토링하여 양식별 프로세서를 사용합니다.
    모든 복잡한 로직은 processors/, converters/, validators/ 모듈에 위임합니다.

    Args:
        template: 플레이스홀더를 포함하는 원본 HTML 템플릿 문자열
        slots_dict: LLM으로부터 추출된 슬롯 이름과 값으로 구성된 딕셔너리
        current_date_iso: 날짜 파싱의 기준이 되는 YYYY-MM-DD 형식의 날짜 문자열
        form_type: 양식 타입 (프로세서 선택용)

    Returns:
        Tuple[str, Dict[str, Any]]:
            - str: 슬롯 값이 채워진 HTML 템플릿 문자열
            - Dict[str, Any]: 최종적으로 처리된 슬롯 딕셔너리
    """
    logging.info(f"Using modular structure for form_type: {form_type}")
    logging.info(f"Initial slots_dict: {slots_dict}")

    if not slots_dict:
        return template, {}

    # 1. 양식별 프로세서 생성
    processor = get_form_processor(form_type)

    # 2. 슬롯 처리 (모든 변환 로직 포함)
    final_processed_slots = processor.process_slots(slots_dict, current_date_iso)

    # 3. HTML 템플릿 채우기
    final_html = processor.fill_template(
        template, final_processed_slots, current_date_iso
    )

    logging.info(f"Modular processing completed for form_type: {form_type}")
    logging.info(f"Final processed slots: {final_processed_slots}")

    return final_html, final_processed_slots


def classify_and_extract_slots_for_template(
    user_input: schema.UserInput,
) -> Dict[str, Any]:
    """사용자 입력을 받아 양식을 분류하고, 해당 양식의 슬롯을 추출한 후,
    템플릿에 채워넣어 반환합니다.
    이제 실제 현재 날짜를 current_date_iso로 사용하여 날짜 관련 처리를 수행합니다.
    """
    logging.info(f"Classifying and extracting slots for input: {user_input.input}")

    # 기준 날짜 설정 (실제 현재 날짜 사용)
    current_date_iso = datetime.now().date().isoformat()
    logging.info(f"Using current_date_iso for processing: {current_date_iso}")

    # 1. 양식 분류
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
            invoke_payload = {
                "input": user_input.input,
            }
            extracted_slots_model = slot_chain.invoke(invoke_payload)
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

        # 4단계: 슬롯 처리 및 템플릿 채우기 (리팩토링된 모듈 구조 사용)
    final_html, final_processed_slots = fill_slots_in_template(
        template=retrieved_template_html,
        slots_dict=raw_slots,
        current_date_iso=current_date_iso,
        form_type=form_type,
    )
    logging.info(
        f"Final processed slots after fill_slots_in_template: {final_processed_slots}"
    )
    # logging.info(f"Final HTML template (first 500 chars): {final_html[:500]}...") # 너무 길면 일부만 로깅

    # 5단계: 최종 결과 반환

    # --- 추가: 결재 정보 조회 로직 --- #
    approver_info_data: Optional[schema.ApproverInfoData] = None
    current_form_config = FORM_CONFIGS.get(form_type)

    # drafterId 동적 할당
    drafter_id = (
        getattr(user_input, "drafterId", None) or "01180001"
    )  # 전달받은 값이 있으면 사용, 없으면 기본값
    if current_form_config and hasattr(current_form_config, "mstPid"):
        mst_pid = current_form_config.mstPid
        approval_request = schema.ApproverInfoRequest(
            mstPid=mst_pid, drafterId=drafter_id
        )
        approval_response = get_approval_info(
            approval_request
        )  # service 내 다른 함수 호출
        if approval_response.code == 1 and approval_response.data:
            approver_info_data = approval_response.data
            logging.info(f"Successfully fetched approver info for mstPid {mst_pid}")
        else:
            logging.warning(
                f"Failed to fetch approver info for mstPid {mst_pid}. Response: {approval_response.message}"
            )
    else:
        logging.warning(
            f"Could not find mstPid for form_type '{form_type}' in FORM_CONFIGS or mstPid attribute missing."
        )
    # --- END 추가: 결재 정보 조회 로직 --- #

    return {
        "form_type": form_type,
        "keywords": keywords,
        "slots": final_processed_slots,  # 최종적으로 변환되고 HTML에 채워진 슬롯
        "html_template": final_html,  # 슬롯 값이 모두 채워진 HTML 문자열
        "original_input": user_input.input,  # 사용자의 원본 입력
        "approver_info": approver_info_data,  # 결재 정보 추가
        "mstPid": (
            mst_pid
            if "mst_pid" in locals() and mst_pid is not None
            else FORM_CONFIGS.get(form_type, {}).get("mstPid")
        ),  # mstPid 추가
        "drafterId": drafter_id,  # drafterId 추가 (실제로는 동적으로 할당)
    }


# 기존 classify_and_get_template 함수는 classify_and_extract_slots_for_template로 대체되었으므로 주석 처리 또는 삭제 가능.
# def classify_and_get_template(user_input: UserInput) -> Dict[str, Any]:
#     ...


# --- 결재자 정보 조회 서비스 --- #
def get_approval_info(
    request: schema.ApproverInfoRequest,  # schema.ApproverInfoRequest로 수정
) -> schema.ApproverInfoResponse:
    """기안자 ID와 양식 ID를 기반으로 결재라인 및 기안자 정보를 조회합니다.
    실제 외부 API를 호출하여 결재 정보를 가져옵니다.
    """
    logging.info(
        f"결재 정보 조회 요청: mstPid={request.mstPid}, drafterId={request.drafterId}"
    )

    api_base_url = os.getenv(
        "APPROVAL_API_BASE_URL", "https://dev-api.ntoday.kr/api/v1/epaper"
    )

    endpoint = "myLine"  # 제공된 코드 참고, 실제 엔드포인트 확인 필요
    url = f"{api_base_url}/{endpoint}"

    params = {"mstPid": request.mstPid, "drafterId": request.drafterId}
    headers = {"Content-Type": "application/json"}

    sample_drafter_name = (
        "홍길동 (API 호출 전)"  # API가 기안자 정보도 반환하면 이 값은 덮어쓰임
    )
    sample_drafter_department = "개발팀 (API 호출 전)"
    approvers = []
    api_call_succeeded = False
    response_message = "API 호출 중 오류 발생"
    response_code = 0  # API 호출 실패 또는 오류 시 기본 코드

    # API 호출 결과로 채워질 변수들 (기안자 정보)
    # API가 기안자 정보를 반환하지 않는 경우를 대비해 기본값 설정
    final_drafter_name = "기안자 정보 없음 (API 미반환)"
    final_drafter_department = "기안자 부서 없음 (API 미반환)"

    try:
        with httpx.Client(timeout=10.0) as client:
            logging.info(f"결재라인 API 호출: POST {url} with params: {params}")
            response = client.post(url, json=params, headers=headers)
            response.raise_for_status()  # HTTP 4xx/5xx 오류 발생 시 예외 발생

            api_response_json = response.json()
            logging.info(f"결재라인 API 응답: {api_response_json}")

            if api_response_json.get("code") == 1 and "data" in api_response_json:
                api_data = api_response_json["data"]

                # API 응답에서 기안자 이름/부서를 가져올 수 있다면 여기서 처리
                # 실제 API 응답의 필드명으로 수정해야 합니다.
                # 예시: final_drafter_name = api_data.get("drafterUserInfo", {}).get("userName", final_drafter_name)
                #       final_drafter_department = api_data.get("drafterUserInfo", {}).get("departmentName", final_drafter_department)
                # 현재 API 응답에는 기안자 정보가 없으므로, 요청받은 drafterId로 임시 정보 생성 또는 고정값 사용
                # 이 부분은 실제 API 명세에 따라 정확히 구현해야 합니다.
                if request.drafterId == "01180001":
                    final_drafter_name = "김기안 (API 요청자)"
                    final_drafter_department = "인사팀 (API 요청자)"
                else:
                    final_drafter_name = f"{request.drafterId} (요청자)"
                    final_drafter_department = "부서 정보 없음"

                # 결재자 목록 파싱 (API 응답 구조에 따라 수정 필요)
                # 제공된 예시: data가 리스트 형태임 (로그에서 확인된 구조)
                if isinstance(api_data, list):
                    for approver_item in api_data:
                        approvers.append(
                            schema.ApproverDetail(
                                aprvPsId=approver_item.get("aprvPsId", "N/A"),
                                aprvPsNm=approver_item.get("aprvPsNm", "N/A"),
                                aprvDvTy=approver_item.get("aprvDvTy", "N/A"),
                                ordr=approver_item.get("ordr", 0),
                            )
                        )
                api_call_succeeded = True
                response_message = api_response_json.get(
                    "message", "결재 라인 조회 성공"
                )
                response_code = api_response_json.get(
                    "code", 1
                )  # API 응답의 코드를 사용
            else:
                response_message = api_response_json.get(
                    "message", "API에서 유효한 데이터를 반환하지 않았습니다."
                )
                logging.warning(
                    f"결재라인 API 응답 코드 또는 데이터 형식 오류: {api_response_json}"
                )

    except httpx.HTTPStatusError as e:
        response_message = (
            f"결재라인 API HTTP 오류: {e.response.status_code} - {e.response.text}"
        )
        logging.error(response_message)
    except httpx.RequestError as e:
        response_message = f"결재라인 API 요청 오류: {e}"
        logging.error(response_message)
    except json.JSONDecodeError as e:
        response_message = f"결재라인 API 응답 JSON 파싱 오류: {e}"
        logging.error(response_message)
    except Exception as e:
        response_message = f"결재라인 정보 처리 중 예외 발생: {e}"
        logging.error(response_message, exc_info=True)
        # api_call_succeeded는 False로 유지, response_code는 0으로 유지

    if api_call_succeeded:
        # API 호출 성공 시: API에서 받아온 approvers 리스트와 기안자 정보 사용
        response_data = schema.ApproverInfoData(
            drafterName=final_drafter_name,  # API 또는 요청 기반으로 설정된 기안자 이름
            drafterDepartment=final_drafter_department,  # API 또는 요청 기반으로 설정된 기안자 부서
            approvers=approvers,  # API에서 파싱한 결재자 목록
        )
    else:
        # API 호출 실패 또는 오류 시: 기존 더미 데이터 생성 로직 사용
        # 이 부분은 fallback으로, 실제 운영에서는 오류 처리를 더 명확히 해야 함
        logging.warning(
            f"API 호출 실패 또는 오류로 인해 더미 결재 정보를 반환합니다. 메시지: {response_message}"
        )
        # 임시 더미 데이터 생성
        sample_drafter_name = "홍길동 (더미)"
        sample_drafter_department = "개발팀 (더미)"
        sample_approvers = []

        if request.drafterId == "01180001":  # 요청 예시와 동일한 경우
            sample_drafter_name = "김기안 (더미)"  # API 실패 시 보여줄 더미 기안자
            sample_drafter_department = "인사팀 (더미)"
            sample_approvers = [
                schema.ApproverDetail(
                    aprvPsId="01160001",
                    aprvPsNm="최순명 (더미)",
                    aprvDvTy="AGREEMENT",
                    ordr=1,
                ),
                schema.ApproverDetail(
                    aprvPsId="01230003",
                    aprvPsNm="최지열 (더미)",
                    aprvDvTy="AGREEMENT",
                    ordr=1,
                ),
                schema.ApproverDetail(
                    aprvPsId="00030005",
                    aprvPsNm="김철수 (더미)",
                    aprvDvTy="APPROVAL",
                    ordr=2,
                ),
            ]
            # mstPid에 따른 분기는 더미 데이터에서 유지할 수 있으나, API 실패 시 일관된 더미를 보여주는 것도 방법

        elif request.drafterId == "dummy_user_002":
            sample_drafter_name = "테스트사용자2 (더미)"
            sample_drafter_department = "기획팀 (더미)"
            sample_approvers = [
                schema.ApproverDetail(
                    aprvPsId="01230003",
                    aprvPsNm="최지열 (더미)",
                    aprvDvTy="APPROVAL",
                    ordr=1,
                )
            ]
        else:
            sample_drafter_name = "알수없음 (더미)"
            sample_drafter_department = "미지정 (더미)"
            # sample_approvers는 비어있음

        response_data = schema.ApproverInfoData(
            drafterName=sample_drafter_name,
            drafterDepartment=sample_drafter_department,
            approvers=sample_approvers,
        )
        # response_code는 이미 0 또는 다른 오류 코드로 설정되어 있을 것임
        # response_message도 오류 메시지로 설정되어 있을 것임

    return schema.ApproverInfoResponse(
        code=response_code, message=response_message, data=response_data
    )


# --- END 결재자 정보 조회 서비스 --- #


# --- 2단계: HTML 폼 데이터 → 최종 API Payload 변환 로직 --- #


def convert_form_data_to_api_payload(form_type: str, form_data: dict) -> dict:
    """폼 데이터를 API 페이로드로 변환하는 통합 함수"""
    logger.info(f"Converting form data to API payload for form_type: {form_type}")
    logger.info(f"Input form_data: {form_data}")

    # 🆕 approvers가 딕셔너리 리스트인 경우 ApproverDetail 객체로 변환
    if "approvers" in form_data and form_data["approvers"]:
        converted_approvers = []
        for approver in form_data["approvers"]:
            if isinstance(approver, dict):
                # 딕셔너리를 ApproverDetail 객체로 변환
                # aprvPsNm이 누락된 경우 기본값 추가
                if "aprvPsNm" not in approver:
                    approver["aprvPsNm"] = ""  # 빈 문자열로 기본값 설정
                converted_approvers.append(schema.ApproverDetail(**approver))
            else:
                # 이미 ApproverDetail 객체인 경우
                converted_approvers.append(approver)
        form_data["approvers"] = converted_approvers
        logger.info(
            f"Converted {len(converted_approvers)} approvers from dict to ApproverDetail objects"
        )

    try:
        # V2 프로세서 사용 시도
        processor = ProcessorFactory.create_processor(form_type)
        if processor and hasattr(processor, "convert_to_api_payload"):
            logger.info(
                f"Using v2 processor for conversion: {processor.__class__.__name__}"
            )
            return processor.convert_to_api_payload(form_data)
        else:
            logger.warning(
                f"No v2 processor found for {form_type}, falling back to legacy conversion"
            )

    except Exception as e:
        logger.warning(f"V2 processor conversion failed for {form_type}: {e}")

    # Legacy 변환 함수들 사용
    legacy_converters = {
        "annual_leave": _convert_annual_leave_to_payload,
        "personal_expense": _convert_personal_expense_to_payload,
        "dinner_expense": _convert_dinner_expense_to_payload,
        "transportation_expense": _convert_transportation_expense_to_payload,
        "inventory_purchase": _convert_inventory_report_to_payload,
        "purchase_approval": _convert_purchase_approval_to_payload,
        "corporate_card": _convert_corporate_card_to_payload,
        "dispatch_report": _convert_dispatch_report_to_payload,
    }

    if form_type in legacy_converters:
        logger.info(f"Using legacy converter for {form_type}")
        return legacy_converters[form_type](form_data)
    else:
        logger.error(f"No converter found for form_type: {form_type}")
        raise ValueError(f"지원하지 않는 양식 타입입니다: {form_type}")


def _convert_annual_leave_to_payload(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """연차 신청서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    # 기존 Legacy API 형식과 동일한 구조 사용
    payload = {
        "mstPid": "1",  # API 명세에 맞게 string 형태로 수정
        "aprvNm": form_data.get("title", "연차 사용 신청"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": form_data.get("reason", "개인 사유"),
        "apdInfo": json.dumps({}, ensure_ascii=False),
        "lineList": [],
        "dayList": [],
        "amountList": [],
    }

    # dayList 구성 (연차 날짜 정보) - 날짜 범위 전체 생성
    start_date = form_data.get("start_date", "")
    end_date = form_data.get("end_date", "")
    leave_type = form_data.get("leave_type", "annual")

    # 휴가 종류를 API dvType으로 변환
    dv_type_map = {
        "annual": "DAY",
        "half_day_morning": "HALF_AM",
        "half_day_afternoon": "HALF_PM",
        "quarter_day_morning": "QUARTER_AM",
        "quarter_day_afternoon": "QUARTER_PM",
    }

    if start_date and end_date:
        try:
            from datetime import datetime, timedelta
            import logging

            # 날짜 문자열을 datetime 객체로 변환
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

            logging.info(f"[연차 신청서] dayList 생성 시작: {start_date} ~ {end_date}")

            if start_dt <= end_dt:
                current_date = start_dt
                while current_date <= end_dt:
                    payload["dayList"].append(
                        {
                            "reqYmd": current_date.isoformat(),  # YYYY-MM-DD 형식
                            "dvType": dv_type_map.get(leave_type, "DAY"),
                        }
                    )
                    current_date += timedelta(days=1)

                logging.info(
                    f"[연차 신청서] dayList 생성 완료: {len(payload['dayList'])}개 날짜"
                )
            else:
                logging.warning(
                    f"[연차 신청서] 잘못된 날짜 순서: start_date({start_date}) > end_date({end_date})"
                )

        except ValueError as e:
            import logging

            logging.error(
                f"[연차 신청서] 날짜 파싱 오류: {e}, start_date={start_date}, end_date={end_date}"
            )
        except Exception as e:
            import logging

            logging.error(f"[연차 신청서] dayList 생성 중 예외 발생: {e}")
    elif start_date:
        # end_date가 없고 start_date만 있는 경우 (당일 휴가)
        payload["dayList"].append(
            {"reqYmd": start_date, "dvType": dv_type_map.get(leave_type, "DAY")}
        )
        logging.info(f"[연차 신청서] 당일 휴가 dayList 생성: {start_date}")
    else:
        import logging

        logging.warning(
            f"[연차 신청서] 시작일이 누락되어 dayList를 생성할 수 없습니다."
        )

    # 결재라인 정보 추가 (API_명세.md에 따라 aprvPslId 사용)
    if "approvers" in form_data and form_data["approvers"]:
        for approver in form_data["approvers"]:
            payload["lineList"].append(
                {
                    "aprvPslId": approver.aprvPsId,  # aprvPslId로 수정
                    "aprvDvTy": approver.aprvDvTy,
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_dinner_expense_to_payload(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """야근 식대 신청서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    # API_명세.md에 따른 표준 구조
    payload = {
        "mstPid": "3",  # API 명세에 맞게 string 형태로 수정
        "aprvNm": form_data.get("title", "야근 식대 신청"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": form_data.get(
            "work_details", form_data.get("notes", "야근 식대 신청")
        ),
        "apdInfo": json.dumps(
            {
                "work_location": form_data.get("work_location", ""),
                "overtime_time": form_data.get("overtime_time", ""),
                "bank_account_for_deposit": form_data.get(
                    "bank_account_for_deposit", ""
                ),
            },
            ensure_ascii=False,
        ),
        "lineList": [],
        "dayList": [],
        "amountList": [],
    }

    # amountList 구성 (비용 정산 정보)
    work_date = form_data.get("work_date", "")
    dinner_amount = form_data.get("dinner_expense_amount", 0)
    work_details = form_data.get("work_details", form_data.get("notes", ""))

    if work_date and dinner_amount:
        payload["amountList"].append(
            {
                "useYmd": work_date,
                "dvNm": "식대",
                "useRsn": work_details,
                "amt": int(dinner_amount) if dinner_amount else 0,
                "qnty": 1,
                "aditInfo": json.dumps({}, ensure_ascii=False),
            }
        )

    # 결재라인 정보 추가 (API_명세.md에 따라 aprvPslId 사용)
    if "approvers" in form_data and form_data["approvers"]:
        for approver in form_data["approvers"]:
            payload["lineList"].append(
                {
                    "aprvPslId": approver.aprvPsId,  # aprvPslId로 수정
                    "aprvDvTy": approver.aprvDvTy,
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_transportation_expense_to_payload(
    form_data: Dict[str, Any],
) -> Dict[str, Any]:
    """교통비 신청서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    purpose = form_data.get("purpose", "")
    notes = form_data.get("notes", "")
    amount_list = form_data.get("amountList", [])

    converted_amount_list = []
    earliest_date = None
    first_origin = ""
    first_destination = ""

    # 영문 타입을 한글표기로 매핑
    type_map = {
        "subway": "지하철",
        "bus": "버스",
        "train": "기차",
        "airplane": "항공",
        "other": "기타",
    }

    for idx, item in enumerate(amount_list):
        transport_type = item.get("transportType", "other")
        origin = item.get("origin", "")
        destination = item.get("destination", "")
        boarding_date = item.get("boardingDate", "")
        amount = int(item.get("amount", 0))

        if idx == 0:
            first_origin = origin
            first_destination = destination
        if boarding_date:
            if earliest_date is None or boarding_date < earliest_date:
                earliest_date = boarding_date

        converted_amount_list.append(
            {
                "useYmd": boarding_date,
                "dvNm": type_map.get(transport_type, "기타"),
                "useRsn": f"{origin} -> {destination}",
                "amt": amount,
                "aditInfo": json.dumps({}, ensure_ascii=False),
            }
        )

    day_list = []  # 교통비 신청서에서는 dayList 사용하지 않음

    apd_info_obj = {
        "origin": first_origin,
        "destination": first_destination,
        "notes": notes,
    }

    payload = {
        "mstPid": "4",
        "aprvNm": form_data.get("title", "교통비 신청서"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": purpose or notes,
        "apdInfo": json.dumps(apd_info_obj, ensure_ascii=False),
        "lineList": [],
        "dayList": [],
        "amountList": converted_amount_list,
    }

    if "approvers" in form_data and form_data["approvers"]:
        for approver in form_data["approvers"]:
            payload["lineList"].append(
                {
                    "aprvPslId": approver.aprvPsId,
                    "aprvDvTy": approver.aprvDvTy,
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_dispatch_report_to_payload(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """파견 및 출장 보고서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    # API_명세.md에 따른 표준 구조
    payload = {
        "mstPid": "5",  # API 명세에 맞게 string 형태로 수정
        "aprvNm": form_data.get("title", "파견 및 출장 보고서"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": form_data.get("purpose", "파견 및 출장 보고서"),
        "apdInfo": json.dumps(
            {
                "departure_date": form_data.get("departure_date", ""),
                "return_date": form_data.get("return_date", ""),
                "destination": form_data.get("destination", ""),
                "accommodation": form_data.get("accommodation", ""),
                "transport_details": form_data.get("transport_details", ""),
            },
            ensure_ascii=False,
        ),
        "lineList": [],
        "dayList": [],
        "amountList": [],
    }

    # dayList 구성 (파견/출장 날짜 정보) - utils.py의 견고한 날짜 처리 활용
    start_date = form_data.get("start_date", "")
    end_date = form_data.get("end_date", "")

    if start_date and end_date:
        try:
            from datetime import datetime, timedelta
            import logging

            # 날짜 문자열을 datetime 객체로 변환
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

            logging.info(
                f"[파견 및 출장 보고서] dayList 생성 시작: {start_date} ~ {end_date}"
            )

            if start_dt <= end_dt:
                current_date = start_dt
                while current_date <= end_dt:
                    payload["dayList"].append(
                        {
                            "reqYmd": current_date.isoformat(),  # YYYY-MM-DD 형식
                            "dvType": "DAY",  # 파견 및 출장 보고서는 DAY로 고정
                        }
                    )
                    current_date += timedelta(days=1)

                logging.info(
                    f"[파견 및 출장 보고서] dayList 생성 완료: {len(payload['dayList'])}개 날짜"
                )
            else:
                logging.warning(
                    f"[파견 및 출장 보고서] 잘못된 날짜 순서: start_date({start_date}) > end_date({end_date})"
                )

        except ValueError as e:
            import logging

            logging.error(
                f"[파견 및 출장 보고서] 날짜 파싱 오류: {e}, start_date={start_date}, end_date={end_date}"
            )
        except Exception as e:
            import logging

            logging.error(f"[파견 및 출장 보고서] dayList 생성 중 예외 발생: {e}")
    else:
        import logging

        logging.warning(
            f"[파견 및 출장 보고서] 시작일 또는 종료일 누락: start_date={start_date}, end_date={end_date}"
        )

    # 결재라인 정보 추가 (API_명세.md에 따라 aprvPslId 사용)
    if "approvers" in form_data and form_data["approvers"]:
        for approver in form_data["approvers"]:
            payload["lineList"].append(
                {
                    "aprvPslId": approver.aprvPsId,
                    "aprvDvTy": approver.aprvDvTy,
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_inventory_report_to_payload(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """비품/소모품 구입내역서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    # API_명세.md에 따른 표준 구조
    payload = {
        "mstPid": "6",  # API 명세에 맞게 string 형태로 수정
        "aprvNm": form_data.get("title", "비품/소모품 구입내역서"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": form_data.get("notes", "비품/소모품 구입"),
        "apdInfo": json.dumps(
            {
                "request_date": form_data.get("request_date", ""),
                "payment_method": form_data.get("payment_method", ""),
            },
            ensure_ascii=False,
        ),
        "lineList": [],
        "dayList": [],
        "amountList": [],
    }

    # amountList 구성 (구매 항목 정보) - 두 가지 경로 지원
    items_to_process = []

    # 1. 1단계에서 추출된 items 배열 사용
    if "items" in form_data and form_data["items"]:
        items_to_process = form_data["items"]
    # 2. 2단계에서 수집된 개별 HTML 필드들 처리
    else:
        for i in range(1, 7):  # 최대 6개 항목
            item_name = form_data.get(f"item_name_{i}")
            if item_name:  # 품명이 있는 경우만 처리
                items_to_process.append(
                    {
                        "item_name": item_name,
                        "item_quantity": form_data.get(f"item_quantity_{i}", 0),
                        "item_unit_price": form_data.get(f"item_unit_price_{i}", 0),
                        "item_total_price": form_data.get(f"item_total_price_{i}", 0),
                        "item_purpose": form_data.get(f"item_purpose_{i}", ""),
                    }
                )

    for item in items_to_process:
        adit_info = {
            "unitPrice": (
                int(item.get("item_unit_price", 0))
                if item.get("item_unit_price")
                else 0
            ),
            "unit": "개",
        }
        payload["amountList"].append(
            {
                "useYmd": form_data.get("request_date", ""),
                "dvNm": item.get("item_name", ""),
                "useRsn": item.get("item_purpose", ""),
                "amt": (
                    int(item.get("item_total_price", 0))
                    if item.get("item_total_price")
                    else 0
                ),
                "qnty": (
                    int(item.get("item_quantity", 0))
                    if item.get("item_quantity")
                    else 0
                ),
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
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_purchase_approval_to_payload(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """구매 품의서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    # API_명세.md에 따른 표준 구조
    payload = {
        "mstPid": "7",  # API 명세에 맞게 string 형태로 수정
        "aprvNm": form_data.get("title", "구매 품의서"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": form_data.get("special_notes", "구매 품의 요청"),
        "apdInfo": json.dumps(
            {
                "draft_department": form_data.get("draft_department", ""),
                "drafter_name": form_data.get("drafter_name", ""),
                "draft_date": form_data.get("draft_date", ""),
                "total_purchase_amount": form_data.get("total_purchase_amount", 0),
                "payment_terms": form_data.get("payment_terms", ""),
                "delivery_location": form_data.get("delivery_location", ""),
                "attached_files_description": form_data.get(
                    "attached_files_description", ""
                ),
                "special_notes": form_data.get("special_notes", ""),
            },
            ensure_ascii=False,
        ),
        "lineList": [],
        "dayList": [],
        "amountList": [],
    }

    # amountList 구성 (구매 품목 정보) - 세 가지 경로 지원
    items_to_process = []

    # 1. 1단계에서 추출된 items 배열 사용
    if "items" in form_data and form_data["items"]:
        items_to_process = form_data["items"]
    # 2. JavaScript processor에서 수집된 purchase_items 배열 사용
    elif "purchase_items" in form_data and form_data["purchase_items"]:
        # purchase_items를 items 형식으로 변환
        for item in form_data["purchase_items"]:
            items_to_process.append(
                {
                    "item_name": item.get("item_name", ""),
                    "item_spec": item.get("item_spec", ""),
                    "item_quantity": item.get("item_quantity", ""),
                    "item_unit_price": item.get("item_unit_price", ""),
                    "item_total_price": item.get("item_total_price", ""),
                    "item_delivery_request_date": item.get("item_delivery_date", ""),
                    "item_supplier": item.get("item_supplier", ""),
                    "item_purpose": item.get("item_notes", ""),
                }
            )
    # 3. 2단계에서 수집된 개별 HTML 필드들 처리
    else:
        for i in range(1, 4):  # 최대 3개 항목
            item_name = form_data.get(f"item_name_{i}")
            item_total_price = form_data.get(f"item_total_price_{i}")
            if item_name and item_total_price:  # 필수 필드가 있는 경우만 처리
                items_to_process.append(
                    {
                        "item_name": item_name,
                        "item_spec": form_data.get(f"item_spec_{i}", ""),
                        "item_quantity": form_data.get(f"item_quantity_{i}", ""),
                        "item_unit_price": form_data.get(f"item_unit_price_{i}", ""),
                        "item_total_price": item_total_price,
                        "item_delivery_request_date": form_data.get(
                            f"item_delivery_date_{i}", ""
                        ),
                        "item_supplier": form_data.get(f"item_supplier_{i}", ""),
                        "item_purpose": form_data.get(f"item_notes_{i}", ""),
                    }
                )

    for item in items_to_process:
        # 납기요청일이 없으면 기안일 사용
        use_date = (
            item.get("item_delivery_request_date")
            or item.get("item_delivery_date")
            or form_data.get("draft_date", "")
        )

        # dvNm 필드에 주요거래처 + 품명 + 규격/사양을 조합
        dvNm_parts = []
        if item.get("item_supplier"):
            dvNm_parts.append(item["item_supplier"])
        if item.get("item_name"):
            dvNm_parts.append(item["item_name"])
        if item.get("item_spec"):
            dvNm_parts.append(item["item_spec"])

        dvNm_combined = " - ".join(filter(None, dvNm_parts))

        adit_info = {
            "unitPrice": (
                int(item.get("item_unit_price", 0))
                if item.get("item_unit_price")
                else 0
            ),
            "unit": "개",
            "item_spec": item.get("item_spec", ""),
            "item_supplier": item.get("item_supplier", ""),
            "item_delivery_request_date": item.get("item_delivery_request_date")
            or item.get("item_delivery_date"),
        }

        payload["amountList"].append(
            {
                "useYmd": use_date,
                "dvNm": dvNm_combined or "품목",  # 빈 값이면 기본값 사용
                "useRsn": item.get("item_purpose", ""),
                "amt": (
                    int(item.get("item_total_price", 0))
                    if item.get("item_total_price")
                    else 0
                ),
                "qnty": (
                    int(item.get("item_quantity", 0))
                    if item.get("item_quantity")
                    else 0
                ),
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
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_personal_expense_to_payload(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """개인 경비 사용내역서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    # API_명세.md에 따른 표준 구조
    payload = {
        "mstPid": "8",  # API 명세에 맞게 string 형태로 수정
        "aprvNm": form_data.get("title", "개인 경비 사용내역서"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": form_data.get("expense_reason", "개인 경비 정산"),
        "apdInfo": json.dumps(
            {
                "total_amount": form_data.get("total_expense_amount", 0),
                "usage_status": form_data.get("usage_status", ""),
            },
            ensure_ascii=False,
        ),
        "lineList": [],
        "dayList": [],
        "amountList": [],
    }

    # amountList 구성 (경비 항목 정보) - 두 가지 경로 지원
    expenses_to_process = []

    # 1. 1단계에서 추출된 expense_items 배열 사용
    if "expense_items" in form_data and form_data["expense_items"]:
        expenses_to_process = form_data["expense_items"]
    # 2. 2단계에서 수집된 개별 HTML 필드들 처리
    else:
        for i in range(1, 4):  # 최대 3개 항목
            expense_date = form_data.get(f"expense_date_{i}")
            expense_amount = form_data.get(f"expense_amount_{i}")
            if expense_date and expense_amount:  # 필수 필드가 있는 경우만 처리
                expenses_to_process.append(
                    {
                        "expense_date": expense_date,
                        "expense_category": form_data.get(f"expense_category_{i}", ""),
                        "expense_description": form_data.get(
                            f"expense_description_{i}", ""
                        ),
                        "expense_amount": expense_amount,
                        "expense_notes": form_data.get(f"expense_notes_{i}", ""),
                    }
                )

    # 분류 매핑 (HTML select value -> 한글명)
    category_mapping = {
        "traffic": "교통비",
        "accommodation": "숙박비",
        "meals": "식대",
        "entertainment": "접대비",
        "education": "교육훈련비",
        "supplies": "소모품비",
        "other": "기타",
    }

    for expense in expenses_to_process:
        # 분류 매핑
        expense_category = expense.get("expense_category", "")
        dvNm = category_mapping.get(expense_category, "기타")

        # useRsn 조합 (사용내역 + 비고)
        expense_description = expense.get("expense_description", "")
        expense_notes = expense.get("expense_notes", "")
        useRsn_parts = []
        if expense_description:
            useRsn_parts.append(expense_description)
        if expense_notes and expense_notes.strip():
            useRsn_parts.append(expense_notes.strip())
        useRsn = " - ".join(useRsn_parts) if useRsn_parts else ""

        payload["amountList"].append(
            {
                "useYmd": expense.get("expense_date", ""),
                "dvNm": dvNm,
                "useRsn": useRsn,
                "amt": (
                    int(expense.get("expense_amount", 0))
                    if expense.get("expense_amount")
                    else 0
                ),
                "qnty": 1,
                "aditInfo": json.dumps({}, ensure_ascii=False),
            }
        )

    # 결재라인 정보 추가
    if "approvers" in form_data and form_data["approvers"]:
        for approver in form_data["approvers"]:
            payload["lineList"].append(
                {
                    "aprvPslId": approver.aprvPsId,
                    "aprvDvTy": approver.aprvDvTy,
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_corporate_card_to_payload(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """법인 카드 사용 내역서 폼 데이터를 API Payload로 변환 (API_명세.md 기준)"""

    # API_명세.md에 따른 표준 구조
    payload = {
        "mstPid": "9",  # API 명세에 맞게 string 형태로 수정
        "aprvNm": form_data.get("title", "법인 카드 사용 내역서"),
        "drafterId": form_data.get("drafterId", "00009"),
        "docCn": form_data.get("expense_reason", "법인카드 사용 정산"),
        "apdInfo": json.dumps(
            {
                "card_number": form_data.get("card_number", ""),
                "card_user_name": form_data.get("card_user_name", ""),
                "expense_reason": form_data.get("expense_reason", ""),
                "statement_date": form_data.get("statement_date", ""),
                "payment_account": form_data.get("payment_account", ""),
            },
            ensure_ascii=False,
        ),
        "lineList": [],
        "dayList": [],
        "amountList": [],
    }

    # amountList 구성 (카드 사용 내역 정보)
    # 방법 1: card_usage_items 배열이 있는 경우 (1단계에서 바로 변환)
    if "card_usage_items" in form_data and form_data["card_usage_items"]:
        # 분류 매핑 (HTML select value -> 한글명)
        category_mapping = {
            "meals": "식대/회식비",
            "traffic_transport": "교통/운반비",
            "supplies": "사무용품비",
            "entertainment": "접대비",
            "utility": "공과금",
            "welfare": "복리후생비",
            "education": "교육훈련비",
            "other": "기타",
        }

        for usage in form_data["card_usage_items"]:
            # 분류 매핑
            usage_category = usage.get("usage_category", "")
            dvNm = category_mapping.get(usage_category, "기타")

            # useRsn 조합 (가맹점명 + 비고)
            usage_description = usage.get("usage_description", "")
            usage_notes = usage.get("usage_notes", "")
            useRsn_parts = []
            if usage_description:
                useRsn_parts.append(usage_description)
            if usage_notes and usage_notes.strip():
                useRsn_parts.append(usage_notes.strip())
            useRsn = " - ".join(useRsn_parts) if useRsn_parts else ""

            payload["amountList"].append(
                {
                    "useYmd": usage.get("usage_date", ""),
                    "dvNm": dvNm,
                    "useRsn": useRsn,
                    "amt": (
                        int(usage.get("usage_amount", 0))
                        if usage.get("usage_amount")
                        else 0
                    ),
                    "qnty": 1,
                    "aditInfo": json.dumps({}, ensure_ascii=False),
                }
            )
    # 방법 2: HTML 폼에서 온 개별 필드들 처리 (2단계에서 변환)
    else:
        # HTML 템플릿의 개별 필드들을 수집하여 amountList 구성
        for i in range(1, 7):  # 최대 6개 항목
            usage_date = form_data.get(f"usage_date_{i}")
            usage_amount = form_data.get(f"usage_amount_{i}")
            merchant_name = form_data.get(f"merchant_name_{i}")
            usage_category = form_data.get(f"usage_category_{i}")
            usage_notes = form_data.get(f"usage_notes_{i}")

            # 필수 필드가 있는 경우만 추가
            if usage_date and usage_amount and merchant_name:
                # 분류 매핑 (HTML select value -> 한글명)
                category_mapping = {
                    "meals": "식대/회식비",
                    "traffic_transport": "교통/운반비",
                    "supplies": "사무용품비",
                    "entertainment": "접대비",
                    "utility": "공과금",
                    "welfare": "복리후생비",
                    "education": "교육훈련비",
                    "other": "기타",
                }
                dvNm = category_mapping.get(usage_category, "기타")

                # useRsn 조합 (가맹점명 + 비고)
                useRsn_parts = [merchant_name]
                if usage_notes and usage_notes.strip():
                    useRsn_parts.append(usage_notes.strip())
                useRsn = " - ".join(useRsn_parts)

                payload["amountList"].append(
                    {
                        "useYmd": usage_date,
                        "dvNm": dvNm,
                        "useRsn": useRsn,
                        "amt": (
                            int(usage_amount) if str(usage_amount).isdigit() else 0
                        ),
                        "qnty": 1,
                        "aditInfo": json.dumps({}, ensure_ascii=False),
                    }
                )

    # 결재라인 정보 추가
    if "approvers" in form_data and form_data["approvers"]:
        for approver in form_data["approvers"]:
            payload["lineList"].append(
                {
                    "aprvPslId": approver.aprvPsId,
                    "aprvDvTy": approver.aprvDvTy,
                    "ordr": approver.ordr,
                }
            )

    return payload


def _convert_leave_type_to_korean(leave_type_value: str) -> str:
    """HTML select 값을 한국어 휴가 종류로 변환"""

    value_to_korean_map = {
        "annual": "연차",
        "half_day_morning": "오전 반차",
        "half_day_afternoon": "오후 반차",
        "quarter_day_morning": "오전 반반차",
        "quarter_day_afternoon": "오후 반반차",
    }

    return value_to_korean_map.get(leave_type_value, leave_type_value)


def _map_expense_category_to_value(category_text: str) -> str:
    """개인 경비 분류 텍스트를 HTML select value로 매핑"""
    if not category_text:
        return ""

    category_lower = category_text.lower()

    # 교통비 관련
    if any(
        keyword in category_lower
        for keyword in [
            "교통",
            "택시",
            "지하철",
            "버스",
            "주차",
            "ktx",
            "항공",
            "유류",
            "톨게이트",
        ]
    ):
        return "traffic"

    # 숙박비 관련
    if any(
        keyword in category_lower
        for keyword in ["숙박", "호텔", "펜션", "게스트하우스", "모텔"]
    ):
        return "accommodation"

    # 식대 관련
    if any(
        keyword in category_lower
        for keyword in [
            "식",
            "음식",
            "커피",
            "음료",
            "카페",
            "식당",
            "회식",
            "점심",
            "저녁",
            "간식",
        ]
    ):
        return "meals"

    # 접대비 관련
    if any(
        keyword in category_lower
        for keyword in [
            "접대",
            "거래처",
            "고객",
            "클라이언트",
            "비즈니스",
            "미팅",
            "상담",
        ]
    ):
        return "entertainment"

    # 교육훈련비 관련
    if any(
        keyword in category_lower
        for keyword in ["교육", "세미나", "연수", "강의", "자격증", "도서"]
    ):
        return "education"

    # 소모품비 관련
    if any(
        keyword in category_lower
        for keyword in ["사무용품", "문구", "소모품", "it용품", "프린터", "복사"]
    ):
        return "supplies"

    # 기타
    return "other"


# --- END 2단계 변환 로직 --- #
