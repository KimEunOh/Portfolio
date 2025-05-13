import os
from together import Together
from dotenv import load_dotenv
from retriever import retrieve_from_local_file
from typing import List, Optional
from pathlib import Path


class RAGChatBot:
    def __init__(self, api_key: str):
        self.client = Together(api_key=api_key)
        self.retriever = None
        self.system_message = """
        You are a helpful assistant that provides accurate answers based on the given context.
        Always use the provided context to answer questions when available.
        If the context doesn't contain relevant information, acknowledge that and provide a general response.
        please answer in Korean.
        """

    def load_knowledge_base(self, folder_path: str) -> None:
        """폴더 내의 모든 PDF 문서를 로드하고 retriever를 초기화합니다."""
        try:
            # Path 객체로 변환
            folder = Path(folder_path)
            if not folder.exists():
                raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder_path}")

            # PDF 파일 목록 가져오기
            pdf_files = list(folder.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError(f"폴더에 PDF 파일이 없습니다: {folder_path}")

            # 각 PDF 파일에 대해 retriever 초기화
            for pdf_file in pdf_files:
                print(f"Loading: {pdf_file.name}")
                if not self.retriever:
                    self.retriever = retrieve_from_local_file(str(pdf_file))
                else:
                    # 기존 retriever에 새로운 문서 추가
                    new_retriever = retrieve_from_local_file(str(pdf_file))
                    # 벡터 저장소 병합 (FAISS의 경우)
                    self.retriever.vectorstore.merge_from(new_retriever.vectorstore)

            print(f"Knowledge base loaded successfully from {folder_path}")
            print(f"Total loaded files: {len(pdf_files)}")

        except Exception as e:
            print(f"Error loading knowledge base: {str(e)}")

    def _get_relevant_context(self, query: str) -> str:
        """질문과 관련된 컨텍스트를 검색합니다."""
        if not self.retriever:
            return ""

        # 관련 문서 검색 (상위 3개)
        documents = self.retriever.get_relevant_documents(query, k=3)
        # 각 문서의 출처 정보 포함
        context_parts = []
        for doc in documents:
            source = doc.metadata.get("source", "Unknown source")
            page = doc.metadata.get("page", "Unknown page")
            context_parts.append(
                f"Source: {source}, Page: {page}\nContent: {doc.page_content}"
            )

        return "\n\n".join(context_parts)

    def get_response(self, prompt: str) -> str:
        """RAG를 활용하여 응답을 생성합니다."""
        # 관련 컨텍스트 검색
        context = self._get_relevant_context(prompt)

        # 프롬프트 구성
        augmented_prompt = self._create_augmented_prompt(prompt, context)

        # API 요청 생성
        response_generator = self.client.chat.completions.create(
            model="Qwen/QwQ-32B",
            messages=[
                {"role": "system", "content": self.system_message},
                {
                    "role": "user",
                    "content": [{"type": "text", "text": augmented_prompt}],
                },
            ],
            temperature=0,
            top_p=0.7,
            top_k=60,
            repetition_penalty=1,
            stop=["<|eot_id|>", "<|eom_id|>"],
            stream=True,
        )

        return self._process_response(response_generator)

    def _create_augmented_prompt(self, prompt: str, context: str) -> str:
        """컨텍스트를 포함한 프롬프트를 생성합니다."""
        if context:
            return f"""
            Context information from multiple documents is below:
            {context}

            Given the context above, please answer the following question:
            {prompt}
            
            Please cite the sources when providing information from the context.
            """
        return prompt

    def _process_response(self, response_generator) -> str:
        """응답 스트림을 처리합니다."""
        response_text = ""
        for token in response_generator:
            if hasattr(token, "choices") and token.choices:
                response_text += token.choices[0].delta.content
            else:
                print("Invalid or empty response:", token)
        return response_text


def main():
    load_dotenv()
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError("API key is not set in the environment variables.")

    # RAG 챗봇 초기화
    bot = RAGChatBot(api_key)

    # documents 폴더의 모든 PDF 파일 로드
    documents_path = "documents"
    bot.load_knowledge_base(documents_path)

    # 대화 루프
    try:
        while True:
            prompt = input("\n질문을 입력하세요 (종료하려면 'quit' 입력): ")
            if prompt.lower() == "quit":
                break

            print("\n답변 생성 중...\n")
            response = bot.get_response(prompt)
            print(response)

    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")


if __name__ == "__main__":
    main()
