import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from retriever import CustomOpenAIEmbeddings, retrieve_from_local_file

# 환경 변수 로드
load_dotenv()


def process_all_documents():
    """documents 디렉토리의 모든 PDF 파일을 처리하여 FAISS 저장소에 추가합니다."""
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

    print(f"처리할 PDF 파일: {len(pdf_files)}")

    # 각 PDF 파일 처리
    success_count = 0
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] 처리 중: {pdf_file.name}")
        try:
            # 파일 처리 및 벡터 저장소 생성
            retriever = retrieve_from_local_file(str(pdf_file))
            print(f"✅ {pdf_file.name} 처리 완료")
            success_count += 1
        except Exception as e:
            print(f"❌ {pdf_file.name} 처리 실패: {str(e)}")
            import traceback

            traceback.print_exc()

    print(f"\n처리 완료: 총 {len(pdf_files)}개 중 {success_count}개 성공")


if __name__ == "__main__":
    process_all_documents()
