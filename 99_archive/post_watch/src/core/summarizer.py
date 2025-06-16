import openai
from src.utils.config import get_config


def summarize_with_openai(text: str) -> str:
    config = get_config()
    client = openai.OpenAI(api_key=config.openai_api_key)
    prompt = f"이 글은, 게임 커뮤니티에서 작성된 자유게시글이야. 해당 글을 3줄 이내로 핵심만 요약해줘. :\n{text}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=128,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[요약 실패] {e}"


def summarize(text: str, summarize_fn=summarize_with_openai) -> str:
    """요약 함수(기본은 OpenAI, 테스트 시 summarize_fn으로 대체 가능)"""
    return summarize_fn(text)
