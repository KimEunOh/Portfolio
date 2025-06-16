import time
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler
from src.utils.config import get_config
from src.db.database import Database
from src.core.crawler import get_posts
from src.core.summarizer import summarize
from src.core.detector import Detector
from src.messenger.discord_sender import send_discord_message
from src.core.comment_crawler import get_top_comments

PC_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
}

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1382969656868081684/bdfh-h5KgroKSFuF8vFrkqxB4xFUMzwvXLX2oZd5TjwNVCXmJx65T81RJOcJEykj8VJa"


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=PC_HEADERS)
    response.raise_for_status()
    html = response.text
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(html)
    return html


def get_post_urls(soup, min_posts=5):
    """게시판 목록에서 URL과 제목만 빠르게 수집 (최소 min_posts개)"""
    posts = []
    for tr in soup.select("div.board-list table tbody tr"):
        a = tr.select_one("td.tit a.subject-link")
        if a:
            title = a.get_text(strip=True)
            url = a["href"]
            if url.startswith("/"):
                url = "https://www.inven.co.kr" + url
            url = url.split("?")[0]  # 쿼리스트링 제거
            posts.append({"title": title, "url": url})
            if len(posts) >= min_posts:
                break
    return posts


def get_post_content(url):
    """상세 페이지에서 본문 내용 추출"""
    print(f"상세 페이지 요청: {url}")
    resp = requests.get(url, headers=PC_HEADERS)
    resp.raise_for_status()
    html = resp.text
    with open("debug_post.html", "w", encoding="utf-8") as f:
        f.write(html)
    soup = BeautifulSoup(html, "html.parser")
    content_div = soup.select_one("div#powerbbsContent")
    if content_div:
        return content_div.get_text(separator="\n", strip=True)
    return ""


def get_post_details(url):
    """상세 페이지에서 본문과 댓글 수집"""
    time.sleep(1)  # 서버 부하 방지
    content = get_post_content(url)
    comments = get_top_comments(url)
    return {"content": content, "comments": comments}


def my_parse_fn(soup):
    """URL 목록 수집 후 DB에 없는 것만 상세 정보 수집"""
    config = get_config()
    db = Database(config.db_path)

    # 1. URL 목록 빠르게 수집 (최소 5개)
    posts = get_post_urls(soup, min_posts=5)
    print(f"수집된 URL 개수: {len(posts)}")

    # 2. DB에 없는 URL만 필터링
    new_posts = []
    processed_urls = set()  # 이미 처리된 URL 추적

    for post in posts:
        url = post["url"]
        if url in processed_urls:
            continue

        if not db.is_post_exists(url):
            new_posts.append(post)
        else:
            print(f"이미 처리된 URL: {url}")

        processed_urls.add(url)

    # 3. 필터링된 URL에 대해서만 상세 정보 수집
    print(f"새로운 URL 개수: {len(new_posts)}")
    for post in new_posts:
        details = get_post_details(post["url"])
        post.update(details)

    db.close()
    return new_posts


def messenger_fn(message, url=None):
    """디스코드로 메시지를 전송합니다."""
    send_discord_message(message)


def main():
    config = get_config()
    db = Database(config.db_path)
    crawler_fn = lambda: get_posts(config.target_url, my_parse_fn)
    detector = Detector(
        crawler_fn=crawler_fn,
        summarizer_fn=lambda text: summarize(text),
        messenger_fn=messenger_fn,
    )
    detector.run_once()
    scheduler = BlockingScheduler()
    scheduler.add_job(detector.run_once, "interval", seconds=30)
    print("[배치] 30초마다 새 글 감지 및 알림 시작!")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("배치 종료")
        db.close()


if __name__ == "__main__":
    main()
