import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
import requests
import json
from dotenv import load_dotenv
from retriever import retrieve_from_local_file
import base64
from PIL import Image
from io import BytesIO
import time
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 전역 변수로 봇 인스턴스 캐시
bot_instance = None

# 이미지 캐시 구현
image_cache = {}

# API 설정
vllm_host = "https://mmxoelfz0q6gnk-8000.proxy.runpod.net"  # 최신 RunPod 프록시 주소
vllm_url = f"{vllm_host}/generate"
REQUEST_TIMEOUT = 120  # 타임아웃을 120초로 증가

# 스레드풀 생성
thread_pool = ThreadPoolExecutor(max_workers=4)


class ImageRAGChatBot:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.retriever = None
        self.system_message = """
        당신은 제공된 문서 컨텍스트만을 기반으로 답변하는 RAG(Retrieval-Augmented Generation) 전문가입니다.
        
        절대적 규칙:
        1. 반드시 제공된 문서 컨텍스트에서 찾은 정보만 사용하세요.
        2. 컨텍스트에 없는 정보는 어떤 경우에도 생성하지 마세요.
        3. 문서 컨텍스트에 있는 정보는 반드시 '[출처: 파일명, 페이지: X]' 형식으로 출처를 인용하세요.
        4. 컨텍스트에 정보가 없다면 "주어진 문서에서 해당 정보를 찾을 수 없습니다"라고 솔직히 답변하세요.
        5. 질문이 제공된 문서 범위를 벗어나면 즉시 "해당 주제는 제공된 문서에서 다루지 않습니다"라고 응답하세요.
        6. 제공된 이미지가 있으면 참조하고 필요시 설명에 포함하세요.
        7. 답변은 항상 한국어로만 작성하세요.
        
        당신의 목표는 오직 문서에 있는 정보만을 정확하게 전달하는 것입니다.
        """
        # 응답 스트리밍 관련 변수
        self.response_queue = asyncio.Queue()

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

    async def _get_relevant_context(self, query: str) -> Dict:
        """비동기 컨텍스트 검색 및 이미지 추출"""
        if not self.retriever:
            print("검색기가 초기화되지 않았습니다.")
            return {"text": "", "images": []}

        try:
            print(f"쿼리로 컨텍스트 검색 중: {query}")
            # 최신 LangChain API와 호환되도록 업데이트
            try:
                # 새로운 invoke 메서드 사용 시도
                documents = self.retriever.invoke(query, config={"k": 3})
                print(f"검색된 문서 수: {len(documents)}")
            except (AttributeError, TypeError) as e:
                # 하위 호환성을 위해 이전 메서드 사용
                print(
                    f"invoke 메서드 사용 실패, 기존 get_relevant_documents 사용: {str(e)}"
                )
                documents = self.retriever.get_relevant_documents(query, k=3)
                print(f"검색된 문서 수: {len(documents)}")

            context_parts = []
            images = []
            image_extraction_tasks = []

            for doc in documents:
                source = doc.metadata.get("source", "Unknown source")
                page = doc.metadata.get("page", "Unknown page")

                # 파일 경로에서 파일명만 추출
                file_name = (
                    source.split("/")[-1]
                    if "/" in source
                    else source.split("\\")[-1] if "\\" in source else source
                )

                context_parts.append(
                    f"[출처: {file_name}, 페이지: {page}]\n{doc.page_content}"
                )

                # PDF에서 이미지 추출 로직 추가 (비동기 처리)
                if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
                    cache_key = f"{source}_{page}"
                    if cache_key in image_cache:
                        # 캐시된 이미지가 있으면 재사용
                        cached_images = image_cache[cache_key]
                        for img_data in cached_images:
                            images.append(
                                {"data": img_data, "source": file_name, "page": page}
                            )
                    else:
                        # 이미지 추출 작업을 비동기 태스크로 등록
                        task = asyncio.create_task(
                            self._extract_images_async(
                                doc.metadata.get("source", ""),
                                doc.metadata.get("page", 1),
                                file_name,
                                page,
                            )
                        )
                        image_extraction_tasks.append(task)

            # 비동기 이미지 추출 작업 완료 대기
            if image_extraction_tasks:
                extracted_images_list = await asyncio.gather(*image_extraction_tasks)
                for extracted_images in extracted_images_list:
                    images.extend(extracted_images)

            print(
                f"컨텍스트 검색 완료: {len(context_parts)} 조각, {len(images)} 이미지"
            )
            return {"text": "\n\n".join(context_parts), "images": images}

        except Exception as e:
            print(f"컨텍스트 검색 오류: {str(e)}")
            import traceback

            traceback.print_exc()
            return {"text": "", "images": []}

    async def _extract_images_async(
        self, pdf_path: str, page_number: int, source: str, page: str
    ) -> List[Dict[str, Any]]:
        """PDF 페이지에서 이미지를 비동기적으로 추출"""
        # 스레드 풀에서 이미지 추출 실행
        loop = asyncio.get_event_loop()
        try:
            extracted_images = await loop.run_in_executor(
                thread_pool, self._extract_images_from_pdf, pdf_path, page_number
            )

            # 결과를 캐시에 저장
            cache_key = f"{source}_{page}"
            image_cache[cache_key] = extracted_images

            # 결과 형식 변환
            return [
                {"data": img_data, "source": source, "page": page}
                for img_data in extracted_images
            ]
        except Exception as e:
            print(f"비동기 이미지 추출 오류: {str(e)}")
            return []

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

    async def get_response(self, prompt: str) -> Dict:
        """기존 동기식 응답 생성 메서드 (비동기 버전)"""
        # 백업 응답 준비
        backup_response = {
            "text": "API 서버에 연결할 수 없습니다. 나중에 다시 시도해주세요.",
            "images": [],
            "sources": [],
        }

        # 컨텍스트 검색 (비동기 처리)
        try:
            context_data = await self._get_relevant_context(prompt)
            # 출처 정보 추출
            sources = self._extract_sources(context_data["text"])
        except Exception as e:
            print(f"컨텍스트 검색 오류: {str(e)}")
            return {
                "text": f"컨텍스트 검색 중 오류가 발생했습니다: {str(e)}",
                "images": [],
                "sources": [],
            }

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
            "temperature": 0.01,  # 더 결정적인 응답을 위해 temperature 낮춤
            "max_tokens": 1024,
            "n": 1,
            "stream": False,  # 일반 응답 요청
        }

        # 디버깅을 위한 컨텍스트 로깅
        print("\n====================== 검색된 컨텍스트 =====================")
        print(
            context_data["text"][:1000] + "..."
            if len(context_data["text"]) > 1000
            else context_data["text"]
        )
        print("===================== 컨텍스트 끝 =====================\n")

        # 출처 정보 디버깅
        print(f"검색된 출처: {sources}")

        # API 연결 시도
        max_retries = 2
        retry_count = 0

        while retry_count < max_retries:
            try:
                # vllm API 호출 (타임아웃 설정 추가)
                print(f"vLLM API 요청 시작: {vllm_url}")
                start_time = time.time()
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(
                        vllm_url, json=payload, timeout=REQUEST_TIMEOUT
                    ),
                )
                elapsed = time.time() - start_time
                print(f"API 응답 시간: {elapsed:.2f}초")
                print(f"API 응답 코드: {response.status_code}")

                response.raise_for_status()
                result = response.json()
                print(f"API 응답 형식: {result.keys()}")

                # 응답 텍스트 추출
                raw_response_text = self._extract_response_text(result)
                if not raw_response_text:
                    raw_response_text = "응답을 받을 수 없습니다."

                # 응답 텍스트 정제
                response_text = self._clean_response(raw_response_text)

                # 최종 응답 로깅
                print("=" * 50)
                print("최종 응답:")
                print(response_text)
                print("출처:", sources)
                print("=" * 50)

                return {
                    "text": response_text,
                    "images": context_data["images"],
                    "sources": sources,
                }

            except requests.exceptions.ConnectionError as e:
                print(f"연결 오류 (시도 {retry_count+1}/{max_retries}): {str(e)}")
                retry_count += 1
                if retry_count < max_retries:
                    print("5초 후 재시도...")
                    await asyncio.sleep(5)
                else:
                    print("최대 재시도 횟수 초과")
                    return {
                        "text": "서버 연결에 실패했습니다. vLLM 서버가 실행 중인지 확인하고 다시 시도해 주세요.",
                        "images": context_data["images"],
                        "sources": sources,
                    }

            except requests.exceptions.Timeout:
                print(f"요청 타임아웃 (시도 {retry_count+1}/{max_retries})")
                retry_count += 1
                if retry_count < max_retries:
                    print("5초 후 재시도...")
                    await asyncio.sleep(5)
                else:
                    print("최대 재시도 횟수 초과")
                    return {
                        "text": "요청 시간이 초과되었습니다. 서버가 응답하지 않습니다.",
                        "images": context_data["images"],
                        "sources": sources,
                    }

            except Exception as e:
                print(f"vllm API 호출 오류: {str(e)}")
                return {
                    "text": f"모델 API 호출 중 오류가 발생했습니다: {str(e)}",
                    "images": context_data["images"],
                    "sources": sources,
                }

    def _create_augmented_prompt(self, prompt: str, context_data: Dict) -> Dict:
        if context_data["text"]:
            return {
                "text": f"""
                다음은 여러 문서에서 가져온 컨텍스트 정보입니다:
                
                {context_data['text']}

                위의 컨텍스트 정보를 반드시 참조하여 다음 질문에 답변하세요:
                {prompt}
                
                *** 중요 지침 ***
                1. 반드시 제공된 컨텍스트 문서에서 찾은 정보만 사용하여 답변하세요.
                2. 컨텍스트에 있는 각 정보의 출처를 명확히 인용하세요 (형식: [출처: 파일명, 페이지: X]).
                3. 컨텍스트에 없는 정보는 알지 못하는 것으로 간주하고 "주어진 문서에서 해당 정보를 찾을 수 없습니다"라고 정직하게 말하세요.
                4. 컨텍스트 외부의 일반 지식을 사용하지 마세요.
                5. 답변은 한국어로만 작성하세요.
                """
            }
        return {"text": prompt}

    async def get_response_stream(self, prompt: str):
        """스트리밍 응답을 위한 비동기 함수"""
        # 응답 큐 초기화
        self.response_queue = asyncio.Queue()

        # 백그라운드에서 응답 생성 작업 시작
        asyncio.create_task(self._generate_response(prompt))

        # 첫 번째 응답이 올 때까지 대기하는 표시
        await self.response_queue.put({"text": "처리 중입니다...", "is_done": False})

        # 응답 스트리밍
        while True:
            response_chunk = await self.response_queue.get()
            # 각 줄에 줄바꿈 문자를 추가하여 클라이언트가 구분할 수 있도록 합니다
            yield json.dumps(response_chunk) + "\n"

            if response_chunk.get("is_done", False):
                break

    async def _generate_response(self, prompt: str):
        """실제 응답을 생성하고 큐에 넣는 함수"""
        try:
            # 컨텍스트 검색 (비동기 처리)
            context_data = await self._get_relevant_context(prompt)

            # 출처 정보 추출
            sources = self._extract_sources(context_data["text"])

            print(f"검색된 출처: {sources}")

            # 응답에 이미지 정보 추가
            await self.response_queue.put(
                {
                    "text": "관련 정보를 찾았습니다. 응답 생성 중...",
                    "is_done": False,
                    "images": context_data["images"],
                    "sources": sources,
                }
            )

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
                "temperature": 0.01,  # 더 결정적인 응답을 위해 temperature 낮춤
                "max_tokens": 1024,
                "n": 1,
                "stream": True,  # 스트리밍 활성화
            }

            # API 연결 시도
            print(f"vLLM API 요청 시작: {vllm_url}")
            start_time = time.time()

            try:
                # 스트리밍 요청
                # 참고: 실제 vLLM 서버가 스트리밍을 지원하지 않을 수 있으므로 대체 로직도 구현
                response = requests.post(
                    vllm_url, json=payload, timeout=REQUEST_TIMEOUT, stream=True
                )
                response.raise_for_status()

                # 스트리밍 응답 처리 (서버가 지원하는 경우)
                if response.headers.get("content-type") == "text/event-stream":
                    accumulated_text = ""
                    for line in response.iter_lines():
                        if line:
                            print(f"받은 응답 라인: {line[:100]}...")  # 디버깅용
                            try:
                                # 데이터 형식에 따라 적절히 처리
                                chunk_text = line.decode("utf-8")
                                if chunk_text.startswith("data: "):
                                    chunk_text = chunk_text[6:]  # 'data: ' 접두사 제거

                                chunk = json.loads(chunk_text)
                                new_text = self._extract_response_text(chunk)

                                if not new_text:
                                    continue

                                # 텍스트 축적 및 정제
                                accumulated_text += new_text
                                cleaned_text = self._clean_response(accumulated_text)

                                # 큐에 추가
                                await self.response_queue.put(
                                    {
                                        "text": cleaned_text,
                                        "is_done": False,
                                        "images": context_data["images"],
                                        "sources": sources,
                                    }
                                )
                            except json.JSONDecodeError as e:
                                print(f"JSON 파싱 오류: {e}, 원본: {line[:100]}...")
                else:
                    # 비스트리밍 응답 처리
                    result = response.json()
                    raw_response_text = self._extract_response_text(result)
                    if not raw_response_text:
                        raw_response_text = "응답을 받을 수 없습니다."

                    # 응답 텍스트 정제
                    response_text = self._clean_response(raw_response_text)

                    # 최종 응답을 큐에 추가
                    await self.response_queue.put(
                        {
                            "text": response_text,
                            "is_done": True,
                            "images": context_data["images"],
                            "sources": sources,
                        }
                    )

                elapsed = time.time() - start_time
                print(f"API 응답 시간: {elapsed:.2f}초")

            except requests.exceptions.ConnectionError as e:
                print(f"연결 오류: {str(e)}")
                await self.response_queue.put(
                    {
                        "text": "서버 연결에 실패했습니다. vLLM 서버가 실행 중인지 확인하고 다시 시도해 주세요.",
                        "is_done": True,
                        "images": context_data["images"],
                        "sources": sources,
                    }
                )
            except requests.exceptions.Timeout:
                print(f"요청 타임아웃")
                await self.response_queue.put(
                    {
                        "text": "요청 시간이 초과되었습니다. 서버가 응답하지 않습니다.",
                        "is_done": True,
                        "images": context_data["images"],
                        "sources": sources,
                    }
                )
            except Exception as e:
                print(f"vllm API 호출 오류: {str(e)}")
                await self.response_queue.put(
                    {
                        "text": f"모델 API 호출 중 오류가 발생했습니다: {str(e)}",
                        "is_done": True,
                        "images": context_data["images"],
                        "sources": sources,
                    }
                )

        except Exception as e:
            print(f"응답 생성 중 오류: {str(e)}")
            await self.response_queue.put(
                {
                    "text": f"오류가 발생했습니다: {str(e)}",
                    "is_done": True,
                    "images": [],
                    "sources": [],
                }
            )

    def _clean_response(self, text: str, full_cleaning: bool = False) -> str:
        """텍스트 정리를 위한 공통 함수"""
        try:
            if not isinstance(text, str):
                if isinstance(text, list):
                    text = "".join([str(item) for item in text])
                else:
                    text = str(text) if text is not None else ""

            # 기본 정리 작업
            text = re.sub(r"\[INST\].*?\[/INST\]", "", text, flags=re.DOTALL)
            text = text.replace("<s>", "").replace("</s>", "")
            text = re.sub(r"\s*\[/INST\]\s*$", "", text)
            text = text.strip()

            # 전체 응답 정리가 필요한 경우 추가 작업 수행
            if full_cleaning:
                # 컨텍스트 정보 제거
                text = re.sub(
                    r"다음은.*?정보입니다:.*?(?=\n\n|$)", "", text, flags=re.DOTALL
                )
                # 이미지 설명 제거
                text = re.sub(r"이미지 \d+:.*?(?=\n\n|$)", "", text, flags=re.DOTALL)
                # 불필요한 공백 및 줄바꿈 정리
                text = re.sub(r"\n\s*\n", "\n\n", text)
                text = re.sub(r"\n{3,}", "\n\n", text)
                text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)
                text = re.sub(r"\s+$", "", text, flags=re.MULTILINE)
                text = re.sub(r"\s+", " ", text)

            return text
        except Exception as e:
            print(f"텍스트 정리 중 오류 발생: {str(e)}")
            return str(text) if text else ""

    def _extract_sources(self, context_text: str) -> List[Dict]:
        """컨텍스트에서 출처 정보를 추출합니다."""
        sources = []
        try:
            # [출처: 파일명, 페이지: 번호] 형식의 패턴 매칭
            pattern = r"\[출처: (.*?), 페이지: (.*?)\]"
            matches = re.finditer(pattern, context_text)

            for match in matches:
                source = {"file": match.group(1), "page": match.group(2)}
                if source not in sources:  # 중복 제거
                    sources.append(source)
        except Exception as e:
            print(f"출처 추출 중 오류 발생: {str(e)}")
        return sources

    def _extract_response_text(self, data: Dict) -> str:
        """다양한 API 응답 형식에서 텍스트 추출"""
        if "text" in data:
            return data["text"]
        elif "outputs" in data and len(data["outputs"]) > 0:
            output = data["outputs"][0]
            if isinstance(output, dict) and "text" in output:
                return output["text"]
            elif isinstance(output, str):
                return output
        elif "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if isinstance(choice, dict):
                if "text" in choice:
                    return choice["text"]
                elif "delta" in choice and "content" in choice["delta"]:
                    return choice["delta"]["content"]
        return ""


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

    response = await bot_instance.get_response(prompt)
    return response


@app.post("/chat_stream")
async def chat_stream(prompt: str = Form(...)):
    """스트리밍 응답을 위한 엔드포인트"""
    global bot_instance

    print(f"스트리밍 요청 받음: {prompt[:50]}...")  # 디버깅

    # 전역 봇 인스턴스가 없으면 초기화
    if bot_instance is None:
        load_dotenv()
        bot_instance = ImageRAGChatBot()
        documents_path = "documents"
        bot_instance.load_knowledge_base(documents_path)
        print("봇 인스턴스 생성 및 지식 베이스 로딩 완료")

    # CORS 및 캐시 설정 추가
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Nginx 프록시 버퍼링 비활성화
    }

    # 스트리밍 응답 생성
    return StreamingResponse(
        bot_instance.get_response_stream(prompt),
        media_type="application/json",
        headers=headers,
    )


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
