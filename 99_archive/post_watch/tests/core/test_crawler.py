import unittest
from unittest.mock import patch
from src.core.crawler import fetch_html, parse_posts, get_posts
from bs4 import BeautifulSoup


def sample_parse_fn(soup: BeautifulSoup):
    # <li class="post"><a href="/post/1">제목1</a></li> 형태를 파싱
    posts = []
    for li in soup.select("li.post"):
        a = li.find("a")
        if a:
            posts.append({"title": a.text.strip(), "url": a["href"]})
    return posts


SAMPLE_HTML = """
<html>
  <body>
    <ul>
      <li class="post"><a href="/post/1">제목1</a></li>
      <li class="post"><a href="/post/2">제목2</a></li>
    </ul>
  </body>
</html>
"""


class TestCrawler(unittest.TestCase):
    def test_parse_posts(self):
        posts = parse_posts(SAMPLE_HTML, sample_parse_fn)
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["title"], "제목1")
        self.assertEqual(posts[0]["url"], "/post/1")
        self.assertEqual(posts[1]["title"], "제목2")
        self.assertEqual(posts[1]["url"], "/post/2")

    @patch("src.core.crawler.fetch_html")
    def test_get_posts(self, mock_fetch_html):
        mock_fetch_html.return_value = SAMPLE_HTML
        url = "http://test.com"
        posts = get_posts(url, sample_parse_fn)
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["title"], "제목1")
        self.assertEqual(posts[1]["url"], "/post/2")


if __name__ == "__main__":
    unittest.main()
