import os
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import requests
import json
from dotenv import load_dotenv
from retriever import retrieve_from_local_file
import base64
from PIL import Image
from io import BytesIO

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 전역 변수로 봇 인스턴스 캐시
bot_instance = None

vllm_host = "http://213.192.2.86:8000"
vllm_url = f"{vllm_host}/generate"


class ImageRAGChatBot:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.retriever = None
        self.system_message = """
        당신은 제공된 컨텍스트를 기반으로 정확한 답변을 제공하는 도우미입니다.
        항상 가능한 경우 제공된 컨텍스트를 사용하여 질문에 답변하세요.
        컨텍스트에 관련 정보가 포함되어 있지 않은 경우 이를 인정하고 일반적인 응답을 제공하세요.
        컨텍스트에 이미지가 제공되면 이미지를 분석하고 응답에 내용을 포함시키세요.
        반드시 한국어로만 답변해야 합니다. 영어 사용은 금지됩니다.
        """

    def load_knowledge_base(self, folder_path: str) -> None:
        try:
            folder = Path(folder_path)
            if not folder.exists():
                raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder_path}")

            pdf_files = list(folder.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError(f"폴더에 PDF 파일이 없습니다: {folder_path}")

            for pdf_file in pdf_files:
                print(f"Loading: {pdf_file.name}")
                if not self.retriever:
                    self.retriever = retrieve_from_local_file(str(pdf_file))
                else:
                    new_retriever = retrieve_from_local_file(str(pdf_file))
                    self.retriever.vectorstore.merge_from(new_retriever.vectorstore)

            print(f"Knowledge base loaded successfully from {folder_path}")
            print(f"Total loaded files: {len(pdf_files)}")

        except Exception as e:
            print(f"Error loading knowledge base: {str(e)}")

    def _get_relevant_context(self, query: str) -> Dict:
        if not self.retriever:
            return {"text": "", "images": []}

        documents = self.retriever.get_relevant_documents(query, k=3)
        context_parts = []
        images = []

        for doc in documents:
            source = doc.metadata.get("source", "Unknown source")
            page = doc.metadata.get("page", "Unknown page")

            # PDF에서 이미지 추출 로직 추가
            if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                try:
                    # PDF 페이지에서 이미지 추출
                    pdf_images = self._extract_images_from_pdf(
                        doc.metadata.get("source", ""), doc.metadata.get("page", 1)
                    )
                    for img_data in pdf_images:
                        images.append(
                            {"data": img_data, "source": source, "page": page}
                        )
                except Exception as e:
                    print(f"이미지 추출 오류: {str(e)}")

            context_parts.append(
                f"Source: {source}, Page: {page}\nContent: {doc.page_content}"
            )

        return {"text": "\n\n".join(context_parts), "images": images}

    def _extract_images_from_pdf(self, pdf_path: str, page_number: int) -> List[str]:
        """PDF 페이지에서 이미지를 추출하고 base64로 인코딩"""
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(
                pdf_path, first_page=page_number, last_page=page_number
            )
            result = []
            for img in images:
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                result.append(img_str)
            return result
        except Exception as e:
            print(f"PDF 이미지 추출 오류: {str(e)}")
            return []

    def get_response(self, prompt: str) -> Dict:
        context_data = self._get_relevant_context(prompt)
        augmented_prompt = self._create_augmented_prompt(prompt, context_data)

        # 이미지 처리를 위한 텍스트 설명 추가
        image_descriptions = []
        if context_data["images"]:
            for i, img in enumerate(context_data["images"]):
                image_descriptions.append(
                    f"이미지 {i+1}: 문서 {img['source']}, 페이지 {img['page']}의 이미지가 있습니다."
                )

        image_text = "\n".join(image_descriptions)
        if image_text:
            prompt_with_images = f"{augmented_prompt['text']}\n\n{image_text}"
        else:
            prompt_with_images = augmented_prompt["text"]

        # vllm API 요청 형식으로 변환
        payload = {
            "prompt": f"<s>[INST] {self.system_message} [/INST]\n\n[INST] {prompt_with_images} [/INST]",
            "temperature": 0.0,
            "top_p": 0.7,
            "top_k": 60,
            "repetition_penalty": 1.0,
            "max_tokens": 1024,
            "stop": ["<|eot_id|>", "<|eom_id|>"],
        }

        try:
            # vllm API 호출
            response = requests.post(vllm_url, json=payload)
            response.raise_for_status()
            result = response.json()

            # 응답 텍스트 추출
            if "text" in result:
                response_text = result["text"]
            else:
                response_text = result.get("outputs", [{}])[0].get(
                    "text", "응답을 받을 수 없습니다."
                )

            return {
                "text": response_text,
                "images": context_data["images"],
            }
        except Exception as e:
            print(f"vllm API 호출 오류: {str(e)}")
            return {
                "text": f"모델 API 호출 중 오류가 발생했습니다: {str(e)}",
                "images": context_data["images"],
            }

    def _create_augmented_prompt(self, prompt: str, context_data: Dict) -> Dict:
        if context_data["text"]:
            return {
                "text": f"""
                다음은 여러 문서에서 가져온 컨텍스트 정보입니다:
                {context_data['text']}

                위의 컨텍스트와 제공된 이미지를 바탕으로 다음 질문에 답변해주세요:
                {prompt}
                
                컨텍스트에서 정보를 제공할 때 출처를 인용해주세요.
                반드시 한국어로만 응답해주세요.
                """
            }
        return {"text": prompt}


# FastAPI 라우트
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
async def chat(prompt: str = Form(...)):
    global bot_instance

    # 전역 봇 인스턴스가 없으면 초기화
    if bot_instance is None:
        load_dotenv()
        bot_instance = ImageRAGChatBot()
        documents_path = "documents"
        bot_instance.load_knowledge_base(documents_path)
        print("봇 인스턴스 생성 및 지식 베이스 로딩 완료")

    response = bot_instance.get_response(prompt)
    return response


# 서버 시작 시 초기화 함수 추가
@app.on_event("startup")
async def startup_event():
    global bot_instance
    try:
        load_dotenv()
        bot_instance = ImageRAGChatBot()
        documents_path = "documents"
        bot_instance.load_knowledge_base(documents_path)
        print("서버 시작 시 봇 인스턴스 초기화 및 지식 베이스 로딩 완료")
    except Exception as e:
        print(f"초기화 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
