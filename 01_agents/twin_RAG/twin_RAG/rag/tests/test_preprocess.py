from ragcore import normalize_text, tokenize, remove_stopwords, preprocess_text


def test_normalize_text_removes_punct_and_lowercases():
    s = "Hello, World! 한국어 테스트."
    out = normalize_text(s)
    assert "hello" in out
    assert "," not in out and "!" not in out


def test_tokenize_and_remove_stopwords():
    s = "This is the test of the system and 한국어 테스트 입니다"
    tokens = preprocess_text(s)
    assert "this" in tokens or "test" in tokens
    assert "the" not in tokens  # stopword
