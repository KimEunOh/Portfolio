"""
RAG (Retrieval Augmented Generation) 모듈.
VectorStore를 사용하여 HTML 템플릿을 검색합니다.
"""

import os
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

# --- VectorStore 설정 --- #
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../templates"))
FAISS_INDEX_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../faiss_index")
)

# 전역 VectorStore 인스턴스 (앱 로드 시 초기화 권장)
vector_store: Optional[FAISS] = None


def _build_or_load_vector_store() -> FAISS:
    """FAISS 인덱스를 로드하거나, 없으면 빌드하고 저장합니다."""
    global vector_store
    if vector_store:
        return vector_store

    embeddings = OpenAIEmbeddings()

    if os.path.exists(FAISS_INDEX_PATH):
        print(f"Loading FAISS index from {FAISS_INDEX_PATH}")
        vector_store = FAISS.load_local(
            FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
        )
        return vector_store

    print(f"Building FAISS index as it does not exist at {FAISS_INDEX_PATH}")
    documents: List[Document] = []
    if not os.path.exists(TEMPLATE_DIR):
        raise FileNotFoundError(f"Template directory not found: {TEMPLATE_DIR}")

    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith(".html"):
            file_path = os.path.join(TEMPLATE_DIR, filename)
            form_type = filename.replace(".html", "").replace("_", " ").title()
            # 예: annual_leave.html -> Annual Leave
            # 실제 form_type과 일치하도록 조정 필요 (현재는 파일명 기반으로 단순 생성)
            # develop-doc.md 에 있는 form_type과 일치 시키려면, 아래와 같이 수정
            if filename == "annual_leave.html":
                form_type = "연차 신청서"
            elif filename == "business_trip.html":
                form_type = "출장비 신청서"
            elif filename == "meeting_expense.html":
                form_type = "회의비 지출결의서"
            elif filename == "other_expense.html":
                form_type = "기타 비용 청구서"
            else:
                form_type = filename.replace(".html", "")  # Fallback

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # 메타데이터에 form_type을 포함시켜 검색 시 활용 가능
            # 검색 쿼리 자체에 form_type을 명시적으로 넣는 것이 더 정확할 수 있음
            documents.append(
                Document(
                    page_content=content,
                    metadata={"form_type": form_type, "source": filename},
                )
            )

    if not documents:
        raise ValueError("No HTML templates found to build vector store.")

    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(FAISS_INDEX_PATH)
    print(f"FAISS index built and saved to {FAISS_INDEX_PATH}")
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
        print("Error: Vector store is not initialized.")
        return None

    # 검색 쿼리 생성 (form_type을 명시적으로 포함)
    query = f"{form_type}"
    if keywords:
        query += " " + " ".join(keywords)

    print(f"RAG Query: {query}")

    try:
        # 가장 유사한 문서 1개 검색
        # retriever = vs.as_retriever(search_kwargs={"k": 1, "filter": {"form_type": form_type}})) # 메타데이터 필터링 예시
        retriever = vs.as_retriever(search_kwargs={"k": 1})
        results = retriever.invoke(query)

        if results:
            print(
                f"RAG Retrieved: {results[0].metadata['source']} for form_type '{results[0].metadata['form_type']}'"
            )
            return results[0].page_content
        else:
            print(f"RAG: No template found for query: {query}")
            return None
    except Exception as e:
        print(f"Error during RAG template retrieval: {e}")
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
