from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, List, Union, Dict
import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import time
import threading
from pydantic import BaseModel, Field

from ragcore.embedder import FakeEmbedder
from ragcore.pipeline import hybrid_search_and_rank
from ragcore.store import NumpyFileVectorStore
from ragcore.websearch import TavilySearchClient, WebSearchError


class DocResult(BaseModel):
    type: str = Field("doc", pattern="^doc$")
    score: float
    index: int
    metadata: Dict[str, Any]
    similarity_raw: float
    similarity_norm: float


class WebResult(BaseModel):
    type: str = Field("web", pattern="^web$")
    score: float
    title: str
    snippet: str
    url: str
    rank: int
    rank_norm: float


class SearchResponse(BaseModel):
    results: List[Union[DocResult, WebResult]]


def _get_store_path() -> str:
    return os.getenv("RAG_STORE_PATH", os.path.join(os.getcwd(), "data", "vectors.npz"))


def create_app() -> FastAPI:
    app = FastAPI(title="Twin RAG API", version="0.1.0")

    # CORS (allow localhost dev by default)
    cors_origins = os.getenv(
        "RAG_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in cors_origins if o.strip()],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging setup
    def _setup_logging() -> logging.Logger:
        level_name = os.getenv("RAG_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_name, logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        return logging.getLogger("twin_rag")

    logger = _setup_logging()

    # Simple singletons for this process
    vector_store = NumpyFileVectorStore(_get_store_path())
    embedder = FakeEmbedder(dim=8)
    web_client = TavilySearchClient()

    # In-memory TTL cache for search results
    # Keyed by (q, doc_top_k, web_count, alpha, beta)
    cache_ttl_sec = float(os.getenv("RAG_CACHE_TTL_SEC", "300"))
    _cache_lock = threading.Lock()
    _cache: Dict[tuple, dict] = {}

    @app.get("/health")
    def health() -> dict:
        logger.debug("health check")
        return {"status": "ok"}

    @app.get("/search", response_model=SearchResponse)
    def search(
        q: str = Query(..., min_length=1, description="query text"),
        doc_top_k: int = Query(5, ge=1, le=50),
        web_count: int = Query(5, ge=0, le=50),
        alpha: float = Query(0.6, ge=0.0, le=1.0),
        beta: float = Query(0.4, ge=0.0, le=1.0),
    ) -> SearchResponse:
        if not q.strip():
            return SearchResponse(results=[])

        # Serve from cache if fresh
        cache_key = (q, doc_top_k, web_count, round(alpha, 4), round(beta, 4))
        now = time.time()
        with _cache_lock:
            entry = _cache.get(cache_key)
            if entry and entry.get("expires_at", 0) > now:
                logger.debug("cache hit for key=%s", cache_key)
                return SearchResponse(results=entry["data"])

        logger.info(
            "search request q=%r doc_top_k=%d web_count=%d alpha=%.3f beta=%.3f",
            q,
            doc_top_k,
            web_count,
            alpha,
            beta,
        )
        try:
            merged = hybrid_search_and_rank(
                q,
                embedder=embedder,
                store=vector_store,
                web_client=web_client,
                doc_top_k=doc_top_k,
                web_count=web_count,
                alpha=alpha,
                beta=beta,
            )
        except WebSearchError as e:
            # Upstream web search layer failed
            logger.exception("web search layer failed: %s", e)
            # Graceful fallback: return doc-only results
            try:
                merged = hybrid_search_and_rank(
                    q,
                    embedder=embedder,
                    store=vector_store,
                    web_client=web_client,
                    doc_top_k=doc_top_k,
                    web_count=0,
                    alpha=alpha,
                    beta=0.0,
                )
            except Exception:
                raise HTTPException(status_code=502, detail=f"Web search error: {e}")

        # Update cache
        with _cache_lock:
            _cache[cache_key] = {"data": merged, "expires_at": now + cache_ttl_sec}
        logger.debug("cache set for key=%s ttl=%s", cache_key, cache_ttl_sec)
        return SearchResponse(results=merged)

    return app


app = create_app()
