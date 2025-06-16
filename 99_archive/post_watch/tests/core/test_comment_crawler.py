import unittest
from src.core.comment_crawler import get_top_comments


class TestCommentCrawler(unittest.TestCase):
    def test_get_top_comments(self):
        # 실제 인벤 게시글 URL (댓글이 충분히 있는 글)
        url = "https://www.inven.co.kr/board/maple/5974/5113313"
        top_n = 3
        comments = get_top_comments(url, top_n=top_n)

        # 반환값이 리스트이고, 각 댓글에 필요한 필드가 있는지 확인
        self.assertIsInstance(comments, list)
        self.assertLessEqual(len(comments), top_n)
        for comment in comments:
            self.assertIn("content", comment)
            self.assertIn("author", comment)
            self.assertIn("up", comment)
            self.assertIsInstance(comment["up"], int)
            self.assertIsInstance(comment["content"], str)
            self.assertIsInstance(comment["author"], str)
            # 추천수 0 이상
            self.assertGreaterEqual(comment["up"], 0)


if __name__ == "__main__":
    unittest.main()
