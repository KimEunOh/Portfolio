import json
import re
import pandas as pd


def extract_responses_split_by_double_newline(
    jsonl_path: str, output_excel: str = "responses.xlsx"
):
    """
    - jsonl_path: assistant 응답이 들어있는 JSONL 파일 경로
    - output_excel: 결과를 저장할 엑셀 파일 이름
    """

    # 정규표현식: 처음 나타나는 큰따옴표 쌍을 찾아서, 바깥 텍스트(그룹1+그룹3)와 안쪽 텍스트(그룹2)를 분리
    pattern = re.compile(r'(.*?)"([^"]+)"(.*)', re.DOTALL)

    rows = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line.strip())
            messages = record.get("messages", [])

            # assistant가 답변한 content만 추출
            assistant_response = None
            for msg in messages:
                if msg.get("role") == "assistant":
                    assistant_response = msg.get("content")
                    break  # 첫 번째 assistant 메시지만 사용(필요시 조정)

            if not assistant_response:
                continue  # assistant 응답이 없는 경우 스킵

            # \n\n(이중 줄바꿈)로 분리
            splitted = assistant_response.split("\n\n")

            # 각 부분을 순회하면서, 큰따옴표 내용을 분리
            for idx, chunk in enumerate(splitted, start=1):
                chunk_str = chunk.strip()
                if not chunk_str:
                    continue  # 빈 문자열이면 스킵

                outside_text = chunk_str
                inside_text = ""

                match = pattern.search(chunk_str)
                if match:
                    # group(1)=큰따옴표 앞, group(2)=큰따옴표 안, group(3)=큰따옴표 뒤
                    outside_before = match.group(1).strip()
                    inside_text = match.group(2).strip()
                    outside_after = match.group(3).strip()

                    # 바깥 텍스트 전체
                    outside_text = (outside_before + " " + outside_after).strip()

                rows.append(
                    {
                        "LineIndex": idx,
                        "OutsideQuotes": outside_text,
                        "InsideQuotes": inside_text,
                    }
                )

    # pandas DataFrame으로 정리
    df = pd.DataFrame(rows, columns=["LineIndex", "OutsideQuotes", "InsideQuotes"])
    df.to_excel(output_excel, index=False)
    print(f"엑셀 파일로 저장 완료: {output_excel}")


if __name__ == "__main__":
    jsonl_file = "testcase.jsonl"  # 모델 응답이 저장된 JSONL 파일
    output_file = "responses.xlsx"  # 결과로 만들 엑셀 파일 이름

    extract_responses_split_by_double_newline(jsonl_file, output_file)
