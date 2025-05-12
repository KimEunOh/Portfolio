import requests
import base64
import os
from pdf2image import convert_from_path
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

system_message = """다음은 PDF에서 추출된 스토리보드 텍스트와, PDF 각 페이지 이미지를 함께 제공할 것이다. 
이 정보들을 종합 분석하여, 사용자가 요청하는 형식에 맞춘 단위 테스트 시나리오를 작성하라.

필수 요구사항:
1. PDF 내 시각적 구성(버튼, 메뉴 위치, UI 요소)과 스토리보드 텍스트를 종합적으로 활용할 것
2. 테스트 시나리오 출력 형식:
   - 단계별 번호를 붙인다. (예: "1. 기능 경로 > 단계 제목   \"테스트 상세 내용\"")
   - 한 줄에 간단한 요약 후, 큰따옴표 안에 '기대 출력'이나 '테스트 상세'를 작성한다.
   - 불필요한 표현(예: AI나 모델이라는 언급, 사족 설명)을 넣지 않는다.
   - 한국어로 작성한다.
3. 가능한 한 많은 예외 상황(필수 항목 누락, 권한 부족, 파일 업로드 실패 등)도 시나리오에 포함할 것

이 규칙에서 벗어나는 내용은 작성하지 않는다."""

prompt_text = """아래는 스토리 보드입니다.

<ImageDisplayed>
{image_url}
</ImageDisplayed>

해당 이미지를 확인하고, 단위 테스트 시나리오를 작성해주세요.

테스트 절차 "기대 출력"

예시 :
1. 사이트관리 > 공지사항 > 목록 화면 > 검색조건 default 확인   "검색조건 default 설정 확인
-게시일 : 접속일 -30일~ 접속일
-구분 : 전체 
-상단고정 : 전체 
-사용여부 : 전체"

1. 사이트관리 > 공지사항 > 목록 화면 > 검색조건 > 전체 버튼 클릭   "전체 버튼 클릭 시 선택 한 날짜 삭제되며 기간 상관없이 검색"
...
- 각 단계는 순서대로 번호를 붙이고
- 한 줄에 간단한 요약 후, 바로 뒤에 큰따옴표 안에 기대 출력(사후 조건 포함) 내용을 적는다.
- 불필요한 AI 표현이나 사족을 넣지 않는다.
- 한국어로 작성한다.
"""


# PDF에서 페이지별 이미지를 추출해 로컬에 저장/또는 메모리로만 처리할 수도 있음.
def pdf_to_images(pdf_path, output_folder="pdf_pages", dpi=200):
    """
    pdf_path      : 변환할 PDF 파일 경로
    output_folder : 변환된 이미지 파일을 저장할 폴더
    dpi           : 이미지 해상도
    return        : 변환된 페이지 이미지 경로 리스트
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pages = convert_from_path(pdf_path, dpi=dpi)
    image_paths = []

    for idx, page in enumerate(pages):
        output_path = os.path.join(output_folder, f"page_{idx+1}.png")
        page.save(output_path, "PNG")
        image_paths.append(output_path)

    return image_paths


def get_processed_images(file_path):
    """
    JSONL 파일에 이미 기록된 image_url(또는 image_data)을 추출해
    재처리를 방지하는 용도로 쓸 수 있는 함수 예시.
    """
    if not os.path.exists(file_path):
        return set()

    processed = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            for message in data["messages"]:
                if message["role"] == "user":
                    # message["content"]가 list인지 dict인지 실제 구조 확인 필요
                    for content_obj in message["content"]:
                        if content_obj["type"] == "image_url":
                            processed.add(content_obj["image_url"]["url"])
    return processed


def process_batch(batch, jsonl_file, client, model="gpt-4o"):
    """
    - batch: 이번에 처리할 이미지 경로 리스트
    - jsonl_file: 결과를 기록할 파일 핸들
    - client: OpenAI client (또는 유사 API 객체)
    - model: 사용할 모델 이름 (기본 예시는 gpt-4o)
    """
    for image_path in batch:
        try:
            print(f"\nProcessing image page: {image_path}")

            # 1) 이미지 로드 후 Base64 인코딩
            with open(image_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            # data:image/jpeg;base64, ... 형태로 구성
            # PDF 페이지라면 PNG 확장자이므로 MIME 타입 "image/png"로 가정
            image_data_url = f"data:image/png;base64,{image_base64}"

            # 2) 모델 호출 (멀티모달 입력)
            #   - 여기서는 'image_url'이라는 필드를 사용하지만,
            #     API 사양에 따라 'image_data' 등을 쓰는 경우도 있음
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": image_data_url}},
                        ],
                    },
                ],
            )

            # 3) 응답 결과 파싱
            # 실제 응답 구조에 맞게 수정해야 함
            response_text = response.choices[0].message.content
            print(f"Response for {image_path}:\n{response_text}")

            # 4) JSONL 포맷으로 저장
            jsonl_data = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": image_path}},
                        ],
                    },
                    {"role": "assistant", "content": response_text},
                ]
            }

            jsonl_file.write(json.dumps(jsonl_data, ensure_ascii=False) + "\n")
            print("Response saved for image page:", image_path)

        except Exception as e:
            print(f"Error processing image {image_path}: {e}")


if __name__ == "__main__":
    # 1) PDF -> 페이지별 이미지 변환
    input_pdf = "문학동네-사이트관리SB.pdf"  # 실제 PDF 파일 경로
    output_pages_folder = "pdf_pages"  # 변환된 페이지 이미지 폴더
    page_images = pdf_to_images(input_pdf, output_pages_folder, dpi=200)

    # 2) OpenAI 클라이언트 준비
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model_name = "gpt-4o"  # 예: gpt-4o, gpt-o1 등등 (실제 환경에 맞춰 변경)

    # 3) 결과 저장 파일
    output_file = "testcase.jsonl"

    # 4) 이미 처리된 이미지(페이지) 확인 (중복 방지용)
    processed_set = get_processed_images(output_file)

    # 5) 배치 사이즈 지정
    batch_size = 2  # 한번에 처리할 페이지 이미지 수

    # 6) JSONL 파일 append 모드로 열기
    with open(output_file, "a", encoding="utf-8") as jsonl_file:
        # 페이지 이미지를 batch_size 단위로 분할
        for i in range(0, len(page_images), batch_size):
            batch = [
                img
                for img in page_images[i : i + batch_size]
                if img not in processed_set
            ]
            if not batch:
                continue  # 이미 처리된 페이지 이미지면 스킵

            process_batch(batch, jsonl_file, client, model_name)
            print(f"Batch {i // batch_size + 1} processed and saved.\n")

            # 배치 간 간격
            time.sleep(2)
