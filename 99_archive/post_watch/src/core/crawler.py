import requests
from bs4 import BeautifulSoup
from typing import Callable, List, Dict


def fetch_html(url: str) -> str:
    """지정한 URL에서 HTML을 가져옵니다."""
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def parse_posts(
    html: str, parse_fn: Callable[[BeautifulSoup], List[Dict]]
) -> List[Dict]:
    """HTML에서 게시물 목록을 추출합니다. parse_fn은 사이트별 파싱 함수입니다."""
    soup = BeautifulSoup(html, "html.parser")
    return parse_fn(soup)


def get_posts(url: str, parse_fn: Callable[[BeautifulSoup], List[Dict]]) -> List[Dict]:
    """URL에서 게시물 목록을 추출합니다."""
    html = fetch_html(url)

    return parse_posts(html, parse_fn)
