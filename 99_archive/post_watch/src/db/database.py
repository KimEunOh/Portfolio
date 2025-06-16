import sqlite3
import datetime
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        """데이터베이스 클래스를 초기화하고 연결을 설정합니다."""
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        """'posts' 테이블이 없으면 생성합니다."""
        query = """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            crawled_at TIMESTAMP NOT NULL,
            is_notified BOOLEAN NOT NULL DEFAULT 0
        );
        """
        try:
            with self.conn:
                self.conn.execute(query)
        except sqlite3.Error as e:
            print(f"테이블 생성 중 오류 발생: {e}")
            raise

    def is_post_exists(self, post_url: str) -> bool:
        """주어진 URL의 게시물이 데이터베이스에 존재하는지 확인합니다."""
        query = "SELECT 1 FROM posts WHERE post_url = ?;"
        cursor = self.conn.cursor()
        cursor.execute(query, (post_url,))
        return cursor.fetchone() is not None

    def add_post(self, post_url: str, title: str):
        """새로운 게시물을 데이터베이스에 추가합니다."""
        if self.is_post_exists(post_url):
            return

        query = """
        INSERT INTO posts (post_url, title, crawled_at, is_notified)
        VALUES (?, ?, ?, ?);
        """
        crawled_at = datetime.datetime.now()
        try:
            with self.conn:
                self.conn.execute(query, (post_url, title, crawled_at, False))
        except sqlite3.IntegrityError:
            # 동시성 문제로 다른 프로세스가 먼저 삽입한 경우
            pass
        except sqlite3.Error as e:
            print(f"게시물 추가 중 오류 발생: {e}")
            raise

    def get_unnotified_posts(self) -> list[dict]:
        """알림이 발송되지 않은 게시물 목록을 가져옵니다."""
        query = "SELECT id, post_url, title FROM posts WHERE is_notified = 0;"
        cursor = self.conn.cursor()
        cursor.execute(query)
        posts = [
            {"id": row[0], "post_url": row[1], "title": row[2]}
            for row in cursor.fetchall()
        ]
        return posts

    def mark_post_as_notified(self, post_id: int):
        """특정 게시물을 '알림 완료' 상태로 업데이트합니다."""
        query = "UPDATE posts SET is_notified = 1 WHERE id = ?;"
        try:
            with self.conn:
                self.conn.execute(query, (post_id,))
        except sqlite3.Error as e:
            print(f"알림 상태 업데이트 중 오류 발생: {e}")
            raise

    def close(self):
        """데이터베이스 연결을 닫습니다."""
        if self.conn:
            self.conn.close()
