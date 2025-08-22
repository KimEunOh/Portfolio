import respx
from httpx import Response
from ragcore import (
    FakeEmbedder,
    NumpyFileVectorStore,
    build_embeddings_for_documents,
    TavilySearchClient,
    hybrid_search_and_rank,
)
from pathlib import Path


def test_build_embeddings_for_documents(tmp_path: Path):
    docs = ["Paragraph one.\n\nParagraph two.", "Another document here."]
    emb = FakeEmbedder(dim=8)
    store = NumpyFileVectorStore(tmp_path / "vecs.npz")
    n = build_embeddings_for_documents(docs, emb, store)
    assert n > 0
    embs, metas = store.load()
    assert embs.shape[0] == n
    assert len(metas) == n


@respx.mock
def test_hybrid_search_and_rank_merges_and_sorts(tmp_path: Path):
    # Prepare small doc store
    docs = [
        "Immigration process guide.",
        "Bank account opening steps.",
        "Korean culture and events.",
    ]
    emb = FakeEmbedder(dim=8)
    store = NumpyFileVectorStore(tmp_path / "vecs.npz")
    build_embeddings_for_documents(docs, emb, store)

    # Mock web results
    endpoint = "https://api.tavily.com/search"
    respx.post(endpoint).mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "title": "Gov Immigration Portal",
                        "content": "Official procedures",
                        "url": "https://gov.example/immigration",
                    },
                    {
                        "title": "Community Guide",
                        "snippet": "Helpful tips",
                        "url": "https://community.example/guide",
                    },
                ]
            },
        )
    )

    client = TavilySearchClient(api_key="x")
    results = hybrid_search_and_rank(
        query="immigration in Korea",
        embedder=emb,
        store=store,
        web_client=client,
        doc_top_k=2,
        web_count=2,
        alpha=0.7,
        beta=0.3,
    )

    assert len(results) >= 2
    # Scores must be in [0,1]
    assert all(0.0 <= r["score"] <= 1.0 for r in results)
    # Ensure types present
    types = {r["type"] for r in results}
    assert "doc" in types and "web" in types

    # Changing weights should change ordering in many cases
    results2 = hybrid_search_and_rank(
        query="immigration in Korea",
        embedder=emb,
        store=store,
        web_client=client,
        doc_top_k=2,
        web_count=2,
        alpha=0.1,
        beta=0.9,
    )
    # Not a hard guarantee, but likely different first item
    assert (
        results[0]["type"] != results2[0]["type"]
        or results[0]["score"] != results2[0]["score"]
    )

    # Remaining assertions handled in a separate test for URL de-duplication


@respx.mock
def test_hybrid_search_and_rank_deduplicates_web_urls(tmp_path: Path):
    docs = ["A doc"]
    emb = FakeEmbedder(dim=8)
    store = NumpyFileVectorStore(tmp_path / "vecs.npz")
    build_embeddings_for_documents(docs, emb, store)

    endpoint = "https://api.tavily.com/search"
    respx.post(endpoint).mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "title": "Gov Immigration Portal",
                        "content": "Official procedures",
                        "url": "https://gov.example/immigration",
                    },
                    {
                        "title": "Gov Immigration Portal 2",
                        "content": "Duplicate",
                        "url": "https://gov.example/immigration",
                    },
                ]
            },
        )
    )
    client = TavilySearchClient(api_key="x")
    results = hybrid_search_and_rank(
        query="immigration in Korea",
        embedder=emb,
        store=store,
        web_client=client,
        doc_top_k=1,
        web_count=3,
        dedupe_web=True,
    )
    web_count_in_results = sum(1 for r in results if r["type"] == "web")
    assert web_count_in_results == 1
