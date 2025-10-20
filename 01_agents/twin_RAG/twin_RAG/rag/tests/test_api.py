from __future__ import annotations

import os
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient

# The app module will import from ragcore. Ensure src on path via pytest.ini
from ragcore.embedder import FakeEmbedder
from ragcore.store import NumpyFileVectorStore


def _bootstrap_test_store(tmp_path: str) -> None:
    store = NumpyFileVectorStore(os.path.join(tmp_path, "vecs.npz"))
    emb = FakeEmbedder(dim=8)
    docs = [
        "Immigration office address and opening hours in Seoul",
        "How to open a bank account in Korea for foreigners",
        "Hospitals with English support near Gangnam",
    ]
    # simple build: chunk as whole docs
    vectors = emb.embed_texts(docs)
    store.add(vectors, [{"doc_id": i, "chunk_id": 0} for i in range(len(docs))])


def _get_test_client(tmp_path: str) -> TestClient:
    # Configure environment so app uses tmp vector store and fake web search key
    os.environ.setdefault("TAVILY_API_KEY", "dummy-key")
    os.environ["RAG_STORE_PATH"] = os.path.join(tmp_path, "vecs.npz")
    from ragapi.main import app  # imported after env vars set

    return TestClient(app)


@pytest.fixture()
def client(tmp_path: str) -> Any:
    _bootstrap_test_store(str(tmp_path))
    return _get_test_client(str(tmp_path))


def test_search_requires_q_param(client: TestClient) -> None:
    r = client.get("/search")
    assert r.status_code == 422  # FastAPI validation error for missing q


def test_search_returns_results(client: TestClient, monkeypatch: Any) -> None:
    # Stub BingSearchClient.search to avoid external calls
    from ragcore import websearch as web_mod

    def fake_search(query: str, count: int = 5, market: str = "en-US"):
        return [
            {
                "title": "Gov page",
                "snippet": "official info",
                "url": "https://gov.example",
            },
            {"title": "Blog", "snippet": "guide", "url": "https://blog.example"},
        ]

    monkeypatch.setattr(web_mod.TavilySearchClient, "search", staticmethod(fake_search))

    r = client.get("/search", params={"q": "bank account"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "results" in data
    assert isinstance(data["results"], list)
    # ensure each item has required keys
    for item in data["results"]:
        assert "type" in item and item["type"] in {"doc", "web"}
        assert "score" in item


def test_search_handles_empty_query(client: TestClient) -> None:
    r = client.get("/search", params={"q": "   "})
    assert r.status_code == 200
    assert r.json() == {"results": []}


def test_search_timeout_error(client: TestClient, monkeypatch: Any) -> None:
    # Force the web client to raise to test error path
    from ragcore import websearch as web_mod

    def raise_err(*args: Any, **kwargs: Any):
        raise web_mod.WebSearchError("timeout")

    monkeypatch.setattr(web_mod.TavilySearchClient, "search", staticmethod(raise_err))

    r = client.get("/search", params={"q": "immigration"})
    # With graceful fallback, request should succeed with doc-only results
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict)
    assert "results" in body
    # ensure results array exists
    assert isinstance(body["results"], list)


def test_search_caching_reuses_web_results(
    client: TestClient, monkeypatch: Any
) -> None:
    # Given: stub web search and count invocations
    from ragcore import websearch as web_mod

    calls = {"count": 0}

    def fake_search(query: str, count: int = 5, market: str = "en-US"):
        calls["count"] += 1
        return [
            {
                "title": "Gov page",
                "snippet": "official info",
                "url": "https://gov.example",
            },
            {"title": "Blog", "snippet": "guide", "url": "https://blog.example"},
        ]

    monkeypatch.setattr(web_mod.TavilySearchClient, "search", staticmethod(fake_search))

    # When: same query is requested twice
    # Use a unique query to avoid interference from cache populated by other tests
    unique_q = "bank account cache unique"
    r1 = client.get(
        "/search",
        params={
            "q": unique_q,
            "doc_top_k": 5,
            "web_count": 5,
            "alpha": 0.6,
            "beta": 0.4,
        },
    )
    assert r1.status_code == 200
    r2 = client.get(
        "/search",
        params={
            "q": unique_q,
            "doc_top_k": 5,
            "web_count": 5,
            "alpha": 0.6,
            "beta": 0.4,
        },
    )
    assert r2.status_code == 200

    # Then: web search is executed only once due to caching
    assert calls["count"] == 1
