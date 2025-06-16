from typing import Callable, Any
from src.core.comment_crawler import get_top_comments
from src.utils.config import get_config
from src.db.database import Database


class Detector:
    def __init__(
        self,
        crawler_fn: Callable[[], list],
        summarizer_fn: Callable[[str], str],
        messenger_fn: Callable[[str, str], Any],
    ):
        """
        :param crawler_fn: 게시물 목록을 반환하는 함수 (예: get_posts)
        :param summarizer_fn: 본문을 요약하는 함수
        :param messenger_fn: 메시지를 전송하는 함수
        """
        self.crawler_fn = crawler_fn
        self.summarizer_fn = summarizer_fn
        self.messenger_fn = messenger_fn

    def run_once(self):
        """한 번 감지 및 처리 사이클을 실행합니다."""
        config = get_config()
        db = Database(config.db_path)
        posts = self.crawler_fn()

        # 구분선 정의
        separator = "=" * 50

        for post in posts:
            url = post["url"]
            title = post["title"]
            if db.is_post_exists(url):
                break

            db.add_post(url, title)
            content = post.get("content", title)
            summary = self.summarizer_fn(content)

            # 댓글 메시지 생성
            comments = post.get("comments", [])
            comment_lines = []
            for idx, c in enumerate(comments, 1):
                comment_lines.append(
                    f"{idx}. (추천 {c['up']}) {c['author']}: {c['content']}"
                )
            comment_block = "\n".join(comment_lines) if comment_lines else "댓글 없음"

            # 최종 메시지 생성 및 전송 (구분선 추가)
            message = (
                f"{separator}\n"
                f"[{title}]\n"
                f"{url}\n"
                f"{summary}\n\n"
                f"[댓글 Top 3]\n"
                f"{comment_block}\n"
                f"{separator}"
            )
            self.messenger_fn(message, url)
        db.close()
