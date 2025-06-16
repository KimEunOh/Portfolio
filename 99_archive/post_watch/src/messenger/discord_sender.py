import requests
import json


def send_discord_message(message: str, url: str = None):
    """디스코드 웹훅으로 메시지를 전송합니다."""
    webhook_url = "https://discord.com/api/webhooks/1382969656868081684/bdfh-h5KgroKSFuF8vFrkqxB4xFUMzwvXLX2oZd5TjwNVCXmJx65T81RJOcJEykj8VJa"

    data = {
        "content": message,
        "username": "Post Watch",
    }

    response = requests.post(
        webhook_url,
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
