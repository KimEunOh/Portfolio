import unittest
import sqlite3
from src.db.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # ':memory:'를 사용하여 테스트마다 새로운 인메모리 DB 생성
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_create_table(self):
        # 테이블이 정상적으로 생성되는지 확인
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='posts';"
        )
        self.assertIsNotNone(cursor.fetchone())

    def test_add_and_check_post(self):
        url = "http://test.com/post1"
        title = "테스트 게시물"
        self.assertFalse(self.db.is_post_exists(url))
        self.db.add_post(url, title)
        self.assertTrue(self.db.is_post_exists(url))

    def test_duplicate_post(self):
        url = "http://test.com/post2"
        title = "중복 테스트"
        self.db.add_post(url, title)
        # 중복 삽입 시 예외 없이 무시되어야 함
        self.db.add_post(url, title)
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts WHERE post_url = ?", (url,))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

    def test_get_unnotified_posts(self):
        url = "http://test.com/post3"
        title = "알림 테스트"
        self.db.add_post(url, title)
        posts = self.db.get_unnotified_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["post_url"], url)

    def test_mark_post_as_notified(self):
        url = "http://test.com/post4"
        title = "알림 완료 테스트"
        self.db.add_post(url, title)
        posts = self.db.get_unnotified_posts()
        self.assertEqual(len(posts), 1)
        post_id = posts[0]["id"]
        self.db.mark_post_as_notified(post_id)
        posts = self.db.get_unnotified_posts()
        self.assertEqual(len(posts), 0)


if __name__ == "__main__":
    unittest.main()
