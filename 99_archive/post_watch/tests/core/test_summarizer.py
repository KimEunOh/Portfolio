import unittest
from src.core.summarizer import summarize


def fake_summarize_fn(text):
    return f"FAKE_SUMMARY:{text[:10]}"


def error_summarize_fn(text):
    raise Exception("API 오류")


class TestSummarizer(unittest.TestCase):
    def test_summarize_success(self):
        text = "이것은 테스트용 본문입니다. 핵심만 요약되어야 합니다."
        result = summarize(text, summarize_fn=fake_summarize_fn)
        self.assertTrue(result.startswith("FAKE_SUMMARY:"))

    def test_summarize_error(self):
        text = "에러 테스트"
        try:
            summarize(text, summarize_fn=error_summarize_fn)
        except Exception as e:
            self.assertEqual(str(e), "API 오류")
        else:
            self.fail("예외가 발생해야 합니다.")


if __name__ == "__main__":
    unittest.main()
