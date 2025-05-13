import os
import sys
from dotenv import load_dotenv
from retriever import CustomOpenAIEmbeddings, retrieve_from_local_file
from pathlib import Path

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 확인
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    sys.exit(1)
else:
    print(f"API 키 확인: {api_key[:5]}...{api_key[-5:]}")

# FAISS 디렉토리 확인 및 생성
faiss_dir = Path("faiss")
if not faiss_dir.exists():
    print(f"FAISS 디렉토리 생성: {faiss_dir}")
    faiss_dir.mkdir(exist_ok=True)
else:
    print(f"FAISS 디렉토리 이미 존재: {faiss_dir}")

# 문서 디렉토리 확인
documents_dir = Path("documents")
if not documents_dir.exists():
    print(f"문서 디렉토리가 존재하지 않습니다: {documents_dir}")
    sys.exit(1)

# 문서 파일 목록
pdf_files = list(documents_dir.glob("*.pdf"))
if not pdf_files:
    print(f"문서 디렉토리에 PDF 파일이 없습니다: {documents_dir}")
    sys.exit(1)

print(f"발견된 PDF 파일: {len(pdf_files)}")
for pdf_file in pdf_files:
    print(f"- {pdf_file.name}")

# 임베딩 모델 테스트
try:
    print("\n임베딩 모델 테스트:")
    embeddings = CustomOpenAIEmbeddings()
    test_text = "이것은 임베딩 테스트입니다."
    result = embeddings.embed_query(test_text)
    print(f"임베딩 성공! 벡터 크기: {len(result)}")
    print(f"벡터 샘플: {result[:5]}...")
except Exception as e:
    print(f"임베딩 오류: {str(e)}")
    sys.exit(1)

# 문서 처리 테스트
print("\n문서 처리 테스트:")
try:
    # 첫 번째 PDF 파일 처리
    first_pdf = str(pdf_files[0])
    print(f"처리 중인 파일: {first_pdf}")
    retriever = retrieve_from_local_file(first_pdf)
    print("벡터 저장소 생성 성공!")

    # 검색 테스트
    test_query = "이 문서는 어떤 내용을 다루나요?"
    print(f"검색 쿼리: {test_query}")
    results = retriever.get_relevant_documents(test_query, k=1)

    if results:
        print(f"검색 결과: {len(results)} 개 찾음")
        doc = results[0]
        source = doc.metadata.get("source", "알 수 없음")
        page = doc.metadata.get("page", "알 수 없음")
        content = (
            doc.page_content[:150] + "..."
            if len(doc.page_content) > 150
            else doc.page_content
        )
        print(f"출처: {source}, 페이지: {page}")
        print(f"내용: {content}")
    else:
        print("검색 결과가 없습니다.")

except Exception as e:
    print(f"문서 처리 오류: {str(e)}")
    import traceback

    traceback.print_exc()

print("\n모든 테스트 완료!")
