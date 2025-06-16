import unittest
from unittest.mock import patch
from src.messenger.discord_sender import send_discord_message


class TestDiscordSender(unittest.TestCase):
    @patch("src.messenger.discord_sender.requests.post")
    def test_send_discord_message_success(self, mock_post):
        mock_post.return_value.status_code = 204
        result = send_discord_message(
            "테스트 메시지", "https://discord.com/api/webhooks/test"
        )
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("src.messenger.discord_sender.requests.post")
    def test_send_discord_message_fail(self, mock_post):
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"
        result = send_discord_message(
            "테스트 메시지", "https://discord.com/api/webhooks/test"
        )
        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch(
        "src.messenger.discord_sender.requests.post", side_effect=Exception("연결 오류")
    )
    def test_send_discord_message_exception(self, mock_post):
        result = send_discord_message(
            "테스트 메시지", "https://discord.com/api/webhooks/test"
        )
        self.assertFalse(result)
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
