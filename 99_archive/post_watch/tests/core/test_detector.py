import unittest
from unittest.mock import MagicMock
from src.core.detector import Detector


class TestDetector(unittest.TestCase):
    def setUp(self):
        # 게시물 2개, 하나는 이미 DB에 존재, 하나는 신규
        self.posts = [
            {"url": "url1", "title": "제목1", "content": "본문1"},
            {"url": "url2", "title": "제목2", "content": "본문2"},
        ]
        # 크롤러 함수는 posts 반환
        self.crawler_fn = MagicMock(return_value=self.posts)
        # DB mock: url1은 이미 존재, url2는 신규
        self.db = MagicMock()
        self.db.is_post_exists.side_effect = lambda url: url == "url1"
        self.db.add_post = MagicMock()
        # 요약 함수는 content를 그대로 반환
        self.summarizer_fn = MagicMock(side_effect=lambda content: f"요약:{content}")
        # 메신저 함수는 호출만 기록
        self.messenger_fn = MagicMock()
        self.detector = Detector(
            self.crawler_fn, self.db, self.summarizer_fn, self.messenger_fn
        )

    def test_run_once(self):
        self.detector.run_once()
        # 신규 게시물(url2)만 DB에 추가
        self.db.add_post.assert_called_once_with("url2", "제목2")
        # 요약 및 메신저도 신규 게시물만 처리
        self.summarizer_fn.assert_called_once_with("본문2")
        self.messenger_fn.assert_called_once_with("[제목2]\n요약:본문2")


if __name__ == "__main__":
    unittest.main()
