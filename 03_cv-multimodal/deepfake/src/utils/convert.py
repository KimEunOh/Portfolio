import json

# 파일 경로 설정
input_filename = r"C:\Users\douly\Documents\keo\LMM\output_data.jsonl"
output_filename = "test_data.jsonl"

# 변환 함수 정의
def transform_data(data):
    # system 메시지 변환
    system_message = {
        "role": "system",
        "content": [{"type": "text", "text": data["messages"][0]["content"]}]
    }
    
    # user 메시지 변환
    user_text_content = data["messages"][1]["content"][0]["text"]
    user_image_content = data["messages"][1]["content"][1]["image_url"]["url"]
    user_message = {
        "role": "user",
        "content": [
            {"type": "text", "text": user_text_content},
            {"type": "image", "image": user_image_content}
        ]
    }
    
    # assistant 메시지 변환
    assistant_text_content = data["messages"][2]["content"]
    assistant_message = {
        "role": "assistant",
        "content": [{"type": "text", "text": assistant_text_content}]
    }
    
    # 새로운 형식으로 messages 리스트 생성
    transformed_data = {
        "messages": [system_message, user_message, assistant_message]
    }
    
    return transformed_data

# JSONL 파일 읽고 변환 후 저장
with open(input_filename, "r", encoding="utf-8") as infile, open(output_filename, "w", encoding="utf-8") as outfile:
    for line in infile:
        data = json.loads(line.strip())  # JSONL 파일의 각 줄을 읽어 Python 객체로 변환
        transformed_data = transform_data(data)  # 데이터 변환
        json.dump(transformed_data, outfile, ensure_ascii=False)  # 변환된 데이터 JSON 형식으로 쓰기
        outfile.write("\n")  # 각 항목을 새 줄에 기록하여 JSONL 형식 유지

print(f"변환된 데이터가 '{output_filename}' 파일에 저장되었습니다.")
