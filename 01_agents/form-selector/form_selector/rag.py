"""
RAG (Retrieval Augmented Generation) 모듈.
VectorStore를 사용하여 HTML 템플릿을 검색합니다.
로컬 파일과 외부 API URL을 모두 지원합니다.
"""

import os
import logging
from typing import List, Optional

import httpx
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# --- VectorStore 설정 --- #
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../templates"))
FAISS_INDEX_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../faiss_index")
)

# form_configs.py에서 FORM_CONFIGS를 가져와서 form_type 매핑에 사용
from .form_configs import FORM_CONFIGS

# 전역 VectorStore 인스턴스 (앱 로드 시 초기화 권장)
vector_store: Optional[FAISS] = None

# 로거 설정
logger = logging.getLogger(__name__)


def fetch_template_from_api(template_url: str) -> Optional[str]:
    """외부 API에서 HTML 템플릿을 가져옵니다."""
    try:
        logger.info(f"Fetching template from external API: {template_url}")
        with httpx.Client(timeout=10.0) as client:
            response = client.get(template_url)
            response.raise_for_status()
            content = response.text
            logger.info(
                f"Successfully fetched template from {template_url} ({len(content)} characters)"
            )
            return content
    except httpx.HTTPStatusError as e:
        logger.error(
            f"HTTP error fetching template from {template_url}: {e.response.status_code} - {e.response.text}"
        )
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error fetching template from {template_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching template from {template_url}: {e}")
        return None


def _build_or_load_vector_store() -> FAISS:
    """FAISS 인덱스를 로드하거나, 없으면 빌드하고 저장합니다.
    로컬 파일과 외부 API URL을 모두 지원합니다."""
    global vector_store
    if vector_store:
        return vector_store

    embeddings = OpenAIEmbeddings()

    if os.path.exists(FAISS_INDEX_PATH):
        logger.info(f"Loading FAISS index from {FAISS_INDEX_PATH}")
        vector_store = FAISS.load_local(
            FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
        )
        return vector_store

    logger.info(f"Building FAISS index as it does not exist at {FAISS_INDEX_PATH}")
    documents: List[Document] = []

    # FORM_CONFIGS에서 템플릿 정보를 가져와서 처리
    for form_name, config in FORM_CONFIGS.items():
        template_path = config.html_template_path

        # 외부 API URL인지 확인
        if template_path.startswith(("http://", "https://")):
            logger.info(
                f"Processing external API template for {form_name}: {template_path}"
            )
            content = fetch_template_from_api(template_path)
            if content:
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"form_type": form_name, "source": template_path},
                    )
                )
                logger.info(f"Added external template '{form_name}' to FAISS documents")
            else:
                logger.warning(
                    f"Failed to fetch external template for {form_name}: {template_path}"
                )
        else:
            # 로컬 파일 처리 (기존 로직)
            if os.path.exists(template_path):
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={"form_type": form_name, "source": template_path},
                        )
                    )
                    logger.info(
                        f"Added local template '{form_name}' to FAISS documents"
                    )
                except Exception as e:
                    logger.error(f"Error reading local template {template_path}: {e}")
            else:
                logger.warning(f"Local template file not found: {template_path}")

    if not documents:
        raise ValueError(
            "No HTML templates (from local files or external APIs) found to build vector store."
        )

    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(FAISS_INDEX_PATH)
    logger.info(
        f"FAISS index built and saved to {FAISS_INDEX_PATH} with {len(documents)} documents"
    )
    return vector_store


# 애플리케이션 시작 시 VectorStore를 로드하거나 빌드합니다.
# 실제 FastAPI 앱에서는 Depends 또는 startup 이벤트에서 호출하는 것이 좋습니다.
# 여기서는 모듈 로드 시 한 번 실행되도록 합니다.
_build_or_load_vector_store()


def retrieve_template(form_type: str, keywords: List[str] = None) -> Optional[str]:
    """
    주어진 form_type과 keywords를 기반으로 VectorStore에서 HTML 템플릿을 검색합니다.
    form_type을 주요 검색어로, keywords를 보조 검색어로 사용합니다.
    """
    vs = _build_or_load_vector_store()
    if not vs:
        logger.error("Error: Vector store is not initialized.")
        return None

    # 검색 쿼리 생성 (form_type을 명시적으로 포함)
    query = f"{form_type}"
    if keywords:
        query += " " + " ".join(keywords)

    logger.info(f"RAG Query: {query}")

    try:
        # 가장 유사한 문서 1개 검색, form_type 메타데이터로 필터링
        retriever = vs.as_retriever(
            search_kwargs={"k": 1, "filter": {"form_type": form_type}}
        )
        results = retriever.invoke(query)

        if results:
            logger.info(
                f"RAG Retrieved: {results[0].metadata['source']} for form_type '{results[0].metadata['form_type']}'"
            )
            return results[0].page_content
        else:
            logger.warning(f"RAG: No template found for query: {query}")
            return None
    except Exception as e:
        logger.error(f"Error during RAG template retrieval: {e}")
        return None


# # 테스트용 코드
# if __name__ == "__main__":
#     # OPENAI_API_KEY 환경변수 설정 필요
#     # from dotenv import load_dotenv
#     # load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")))

#     # vector_store를 먼저 빌드/로드합니다.
#     _build_or_load_vector_store()

#     # 테스트 검색
#     # retrieved_html = retrieve_template("연차 신청서", ["2일", "휴가"])
#     retrieved_html = retrieve_template("출장비 신청서", ["대전", "경비"])
#     if retrieved_html:
#         print("\nRetrieved HTML (부분 출력):\n", retrieved_html[:200] + "...")
#     else:
#         print("\nNo HTML retrieved.")
