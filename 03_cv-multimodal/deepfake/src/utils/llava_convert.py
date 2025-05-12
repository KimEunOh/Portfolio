import uuid
import json


# Define the function to process the input JSONL file and transform its content
def process_jsonl(input_file_path, output_file_path):
    converted_data = []

    # Generate a unique 4-digit ID
    def generate_id():
        return str(uuid.uuid4().int)[:4]

    # Read the input JSONL file and process each entry
    with open(input_file_path, "r", encoding="utf-8") as file:
        for line in file:
            entry = json.loads(line.strip())
            system_prompt = ""
            user_prompt = ""
            image_url = "unknown.jpg"
            gpt_value = ""

            # Extract relevant fields from the JSONL structure
            for message in entry.get("messages", []):
                if message["role"] == "system":
                    system_prompt = message["content"]
                elif message["role"] == "user":
                    for content in message["content"]:
                        if content["type"] == "text":
                            user_prompt = content["text"]
                        elif content["type"] == "image_url":
                            image_url = content["image_url"]["url"]
                elif message["role"] == "assistant":
                    gpt_value = message["content"]

            # Create the new formatted entry
            new_entry = {
                "id": generate_id(),
                "image": image_url.split("/")[
                    -1
                ],  # Use the last part of the URL as the image file name
                "conversations": [
                    {
                        "from": "human",
                        "value": f"System prompt: {system_prompt}\nUser prompt: {user_prompt}",
                    },
                    {"from": "gpt", "value": gpt_value},
                ],
            }
            converted_data.append(new_entry)

    # Write the transformed data to the output JSONL file
    with open(
        output_file_path, "w", encoding="utf-8"
    ) as output_file:  # UTF-8로 파일 저장
        for entry in converted_data:
            output_file.write(json.dumps(entry) + "\n")


# Input and output file paths
input_file_path = "output_data.jsonl"
output_file_path = "llava_data.jsonl"

# Process the file
process_jsonl(input_file_path, output_file_path)

output_file_path
