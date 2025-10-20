import re
from typing import Iterable, List

# Minimal bilingual stopword set (EN/KR). Extend as needed.
EN_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "at",
    "by",
    "from",
    "that",
    "this",
    "it",
}
KR_STOPWORDS = {
    "그리고",
    "또는",
    "하지만",
    "또",
    "이",
    "그",
    "저",
    "것",
    "수",
    "등",
    "및",
    "또한",
    "하게",
    "하게끔",
    "위해",
    "에서",
    "으로",
    "에",
    "의",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
}
STOPWORDS = EN_STOPWORDS | KR_STOPWORDS

# Basic punctuation removal (portable across Python stdlib)
_basic_punct_re = re.compile(r"[\.,\-\—\–!?;:'\"\(\)\[\]{}<>/\\\n\r\t]")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    lowered = text.lower()
    return _basic_punct_re.sub(" ", lowered)


def tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [t for t in text.split() if t]


def remove_stopwords(tokens: Iterable[str]) -> List[str]:
    return [t for t in tokens if t not in STOPWORDS]


def preprocess_text(text: str) -> List[str]:
    return remove_stopwords(tokenize(normalize_text(text)))
