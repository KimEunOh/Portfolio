import os
from pathlib import Path
from typing import List, Dict, Any, Union
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import openai
import numpy as np


class CustomOpenAIEmbeddings:
    """OpenAI API를 직접 사용하는 임베딩 클래스"""

    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.model = model
        if api_key:
            openai.api_key = api_key
        elif os.getenv("OPENAI_API_KEY"):
            openai.api_key = os.getenv("OPENAI_API_KEY")
        else:
            raise ValueError("OpenAI API 키가 필요합니다.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """문서 목록을 임베딩합니다."""
        if not texts:
            return []

        # 각 텍스트를 최대 토큰 수에 맞게 자르기
        processed_texts = [text[:8191] for text in texts]  # 대략 8K 토큰 제한에 맞춤

        try:
            # OpenAI API를 직접 호출
            response = openai.embeddings.create(model=self.model, input=processed_texts)
            # 임베딩 벡터 추출
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            print(f"OpenAI 임베딩 오류: {str(e)}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """검색 쿼리를 임베딩합니다."""
        if not text:
            return [0.0] * 1536  # 빈 쿼리에 대한 기본 벡터 반환

        text = text[:8191]  # 대략 8K 토큰 제한에 맞춤
        embeddings = self.embed_documents([text])
        return embeddings[0]

    def __call__(
        self, text: Union[str, List[str]]
    ) -> Union[List[float], List[List[float]]]:
        """LangChain과 호환되는 호출 인터페이스"""
        if isinstance(text, str):
            return self.embed_query(text)
        elif isinstance(text, list):
            return self.embed_documents(text)
        else:
            raise ValueError(f"텍스트 타입이 잘못되었습니다: {type(text)}")


class CustomRetriever:
    """커스텀 검색기 클래스"""

    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    def get_relevant_documents(self, query: str, k: int = 3) -> List[Any]:
        """쿼리와 관련된 문서를 검색합니다."""
        return self.vectorstore.similarity_search(query, k=k)

    # LangChain 0.3.x 호환 메서드
    def invoke(self, query: str, config: Dict = None) -> List[Any]:
        """쿼리와 관련된 문서를 검색합니다."""
        if config and "k" in config:
            return self.get_relevant_documents(query, k=config["k"])
        return self.get_relevant_documents(query)


def retrieve_from_local_file(file_path: str) -> CustomRetriever:
    """파일에서 검색기를 생성합니다."""
    if not os.path.exists("faiss"):
        os.makedirs("faiss")

    # 환경 변수 로드
    load_dotenv()

    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    # 문서 로드
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # 텍스트 청크 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    print(f"문서 청크 수: {len(chunks)}")

    try:
        print("OpenAI 임베딩 모델 초기화 시작...")
        embeddings = CustomOpenAIEmbeddings()
        print("OpenAI 임베딩 모델 초기화 완료!")

        print("벡터 저장소 생성 시작...")
        vectorstore = FAISS.from_documents(chunks, embedding=embeddings)
        print("벡터 저장소 생성 완료!")

        retriever = CustomRetriever(vectorstore)
        return retriever

    except Exception as e:
        print(f"임베딩 처리 중 오류 발생: {str(e)}")
        raise
