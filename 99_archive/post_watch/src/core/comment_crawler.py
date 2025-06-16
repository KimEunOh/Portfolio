import requests
from bs4 import BeautifulSoup
import re
import logging
import time

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_top_comments(url, top_n=3):
    """인벤 게시글의 상위 추천 댓글을 가져옵니다."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        logger.info(f"댓글 수집 시작: {url}")

        # 페이지 요청
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # HTML 파싱
        soup = BeautifulSoup(response.text, "html.parser")

        # 댓글 아이템 추출
        comments = []
        for item in soup.select("div.replyList div.reply"):
            try:
                # 작성자 정보
                author = item.select_one("div.replySubject span.nickname")
                if not author:
                    continue
                author = author.get_text(strip=True)

                # 댓글 내용
                content = item.select_one("div.replyContent")
                if not content:
                    continue
                content = content.get_text(strip=True)

                # 추천수 (숫자만 추출)
                up_tag = item.select_one("button.btn_up span")
                up = 0
                if up_tag:
                    up_text = up_tag.get_text(strip=True)
                    up_match = re.search(r"\d+", up_text)
                    if up_match:
                        up = int(up_match.group())

                comments.append({"content": content, "author": author, "up": up})

            except Exception as e:
                logger.error(f"댓글 파싱 중 오류: {str(e)}")
                continue

        # 추천수 기준 정렬
        comments.sort(key=lambda x: x["up"], reverse=True)

        logger.info(f"수집된 댓글 수: {len(comments)}")
        return comments[:top_n]

    except Exception as e:
        logger.error(f"댓글 수집 중 오류 발생: {str(e)}")
        return []
