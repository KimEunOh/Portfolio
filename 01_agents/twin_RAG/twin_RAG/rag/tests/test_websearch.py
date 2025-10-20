import json
import respx
from httpx import Response
from ragcore import TavilySearchClient


@respx.mock
def test_tavily_search_success_parses_results():
    endpoint = "https://api.tavily.com/search"
    respx.post(endpoint).mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "title": "Example Title",
                        "content": "Short summary",
                        "url": "https://example.com",
                    },
                    {
                        "title": "Second",
                        "snippet": "Desc fallback",
                        "url": "https://example.org",
                    },
                ]
            },
        )
    )
    client = TavilySearchClient(api_key="test-key")
    results = client.search("korean immigration guide", count=2)
    assert len(results) == 2
    assert results[0]["title"] == "Example Title"
    assert results[0]["snippet"] == "Short summary"
    assert results[0]["url"] == "https://example.com"
    assert results[1]["snippet"] == "Desc fallback"


@respx.mock
def test_tavily_search_invalid_key_raises():
    endpoint = "https://api.tavily.com/search"
    respx.post(endpoint).mock(return_value=Response(401, json={"error": "bad key"}))
    client = TavilySearchClient(api_key="bad-key")
    try:
        client.search("test")
        assert False, "Expected error"
    except Exception as e:
        assert "Invalid" in str(e)


@respx.mock
def test_tavily_search_empty_query_returns_empty_list():
    client = TavilySearchClient(api_key="x")
    assert client.search("   ") == []
