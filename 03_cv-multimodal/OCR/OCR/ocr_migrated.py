import os
import re
import time
import argparse
import json
import pandas as pd
from collections import defaultdict
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai


def configure_api():
    """환경 변수에서 API 키를 로드하고 Gemini 모델을 설정합니다."""
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("'.env' 파일에서 GOOGLE_API_KEY를 찾을 수 없습니다.")
    genai.configure(api_key=google_api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def extract_data_from_image(model, image_path):
    """
    이미지 경로를 받아 구조화된 데이터를 요청하고 JSON 텍스트를 반환합니다.
    """
    try:
        # 프롬프트 파일을 읽어옵니다.
        try:
            with open("prompt.txt", "r", encoding="utf-8") as f:
                prompt_text = f.read()
        except FileNotFoundError:
            print(
                "❌ 'prompt.txt' 파일을 찾을 수 없습니다. 스크립트와 같은 위치에 있는지 확인해주세요."
            )
            return None

        img = Image.open(image_path)
        # img = img.convert("L")  # Grayscale conversion, if needed.
        print(f"이미지 열기 성공: {image_path}, 크기: {img.size}")

        response = model.generate_content([prompt_text, img])
        print(f"모델 응답 수신 완료.")
        return response.text
    except Exception as e:
        print(f"오류 발생: {e}")
        return None


def process_images_from_folder(model, folder_path, batch_size, delay_seconds):
    """
    폴더 내 모든 이미지 파일을 처리하고 추출된 데이터를 CSV 파일에 저장합니다.
    """
    category_data = defaultdict(list)
    image_files = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".jfif")):
                image_files.append(os.path.join(root, file))

    print(f"총 처리할 이미지 파일 수: {len(image_files)}")

    for batch_idx, i in enumerate(range(0, len(image_files), batch_size)):
        batch_files = image_files[i : i + batch_size]

        if batch_idx > 0:
            print(f"\n⏳ API 사용량 조절을 위해 {delay_seconds}초 대기 중...")
            time.sleep(delay_seconds)

        print(
            f"\n🔄 배치 {batch_idx+1} 처리 시작 (파일 {i+1}~{min(i+batch_size, len(image_files))})"
        )

        for image_path in batch_files:
            print(f"\n🚀 처리 중: {image_path}")

            filename = os.path.basename(image_path)
            rel_path = os.path.relpath(image_path, folder_path)
            parts = rel_path.split(os.sep)

            if len(parts) > 1:
                category = parts[0]
            else:
                match = re.search(r"[가-힣]+ ([가-힣]+)", filename)
                category = match.group(1) if match else "기타"

            result = extract_data_from_image(model, image_path)

            if result:
                # 응답 문자열에서 JSON 부분만 정리하여 추출
                cleaned_result = result.strip()
                json_str = cleaned_result
                if cleaned_result.startswith("```json"):
                    json_str = cleaned_result[7:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                json_str = json_str.strip()

                print(f"\n📌 반환 JSON ({filename}):\n{json_str}")

                try:
                    # JSON 문자열을 파이썬 객체(리스트)로 변환
                    extracted_data = json.loads(json_str)

                    if isinstance(extracted_data, list):
                        for item in extracted_data:
                            item["파일명"] = filename  # 출처 파일명 추가
                            category_data[category].append(item)
                    else:
                        print(
                            f"⚠️ JSON 형식이 리스트가 아닙니다: {type(extracted_data)}"
                        )

                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 파싱 오류가 발생했습니다: {e}")
            else:
                print("결과를 받지 못했습니다.")

    for category, data in category_data.items():
        if data:
            df = pd.DataFrame(data)
            output_csv = f"{category}.csv"
            df.to_csv(output_csv, index=False, encoding="utf-8-sig")
            print(
                f"\n✅ '{category}' 카테고리 정보가 '{output_csv}' 파일에 저장되었습니다. (총 {len(df)}개)"
            )

    all_data = [item for sublist in category_data.values() for item in sublist]
    if all_data:
        df_all = pd.DataFrame(all_data)
        output_csv = "전체_추출_데이터.csv"
        df_all.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(
            f"\n✅ 모든 추출 정보가 '{output_csv}' 파일에 저장되었습니다. (총 {len(df_all)}개)"
        )


def main():
    """메인 함수: 인자를 파싱하고 이미지 처리를 시작합니다."""
    parser = argparse.ArgumentParser(
        description="Gemini를 사용하여 이미지에서 구조화된 데이터를 추출합니다."
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="image/",
        help="이미지 파일이 포함된 폴더 경로",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=10,
        help="딜레이 전 처리할 이미지 개수",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=60,
        help="API 사용량 조절을 위한 배치 간 대기 시간(초)",
    )
    args = parser.parse_args()

    try:
        model = configure_api()
        process_images_from_folder(model, args.folder, args.batch_size, args.delay)
    except Exception as e:
        print(f"스크립트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
