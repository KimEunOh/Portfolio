from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, TypedDict, Dict, Any
import numpy as np

from .embedder import BaseEmbedder
from .store import NumpyFileVectorStore
from .websearch import TavilySearchClient, WebResult


Chunker = Callable[[str], List[str]]


def default_chunker(text: str, max_chars: int = 800) -> List[str]:
    chunks: List[str] = []
    buf: List[str] = []
    size = 0
    for line in text.splitlines():
        if size + len(line) + 1 > max_chars and buf:
            chunks.append("\n".join(buf).strip())
            buf, size = [], 0
        buf.append(line)
        size += len(line) + 1
    if buf:
        chunks.append("\n".join(buf).strip())
    return [c for c in chunks if c]


@dataclass
class BuildConfig:
    chunker: Chunker = default_chunker


def build_embeddings_for_documents(
    documents: Sequence[str],
    embedder: BaseEmbedder,
    store: NumpyFileVectorStore,
    config: BuildConfig | None = None,
) -> int:
    cfg = config or BuildConfig()
    all_chunks: List[str] = []
    metadatas: List[dict] = []
    for i, doc in enumerate(documents):
        chunks = cfg.chunker(doc)
        all_chunks.extend(chunks)
        metadatas.extend({"doc_id": i, "chunk_id": j} for j in range(len(chunks)))
    if not all_chunks:
        return 0
    embeddings = embedder.embed_texts(all_chunks)
    store.add(embeddings, metadatas)
    return embeddings.shape[0]


# --------------------
# Hybrid search & rank
# --------------------


class HybridDocEntry(TypedDict):
    type: str  # "doc"
    score: float
    index: int
    metadata: Dict[str, Any]
    similarity_raw: float
    similarity_norm: float


class HybridWebEntry(TypedDict):
    type: str  # "web"
    score: float
    title: str
    snippet: str
    url: str
    rank: int
    rank_norm: float


def _scale_cosine_to_unit(x: float) -> float:
    # cosine in [-1,1] -> [0,1]
    return max(0.0, min(1.0, (x + 1.0) / 2.0))


def _scale_rank_to_unit(rank: int, total: int) -> float:
    # 1-based rank: best=1 -> 1.0, worst=total -> 1/total
    total = max(1, total)
    rank = max(1, rank)
    return (total - rank + 1) / total


def hybrid_search_and_rank(
    query: str,
    embedder: BaseEmbedder,
    store: NumpyFileVectorStore,
    web_client: TavilySearchClient,
    *,
    doc_top_k: int = 5,
    web_count: int = 5,
    alpha: float = 0.6,
    beta: float = 0.4,
    dedupe_web: bool = True,
) -> List[HybridDocEntry | HybridWebEntry]:
    """Combine document similarity and web rank into a single ranked list.

    - Document score: cosine similarity scaled to [0,1]
    - Web score: linear rank scaling to [0,1]
    - Final: alpha * doc + beta * web (missing component treated as 0)
    """
    if not query.strip():
        return []

    # Document side
    q_emb = embedder.embed_texts([query])
    doc_results = store.search(q_emb, top_k=doc_top_k)
    embeddings, metadatas = store.load()
    doc_entries: List[HybridDocEntry] = []
    if doc_results and len(doc_results[0]) > 0:
        for idx, sim in doc_results[0]:
            sim_norm = _scale_cosine_to_unit(float(sim))
            meta = metadatas[idx] if 0 <= idx < len(metadatas) else {}
            doc_entries.append(
                HybridDocEntry(
                    type="doc",
                    score=alpha * sim_norm,
                    index=int(idx),
                    metadata=dict(meta),
                    similarity_raw=float(sim),
                    similarity_norm=float(sim_norm),
                )
            )

    # Web side
    web_raw: List[WebResult] = []
    if web_count > 0:
        web_raw = web_client.search(query, count=web_count)
    web_entries: List[HybridWebEntry] = []
    if web_raw:
        # Optional dedup by URL while preserving order
        seen: set[str] = set()
        unique_items: List[WebResult] = []
        for item in web_raw:
            url = item.get("url", "")
            if not url:
                continue
            if dedupe_web and url in seen:
                continue
            seen.add(url)
            unique_items.append(item)
        total = len(unique_items)
        for i, item in enumerate(unique_items, start=1):
            r_norm = _scale_rank_to_unit(i, total)
            web_entries.append(
                HybridWebEntry(
                    type="web",
                    score=beta * r_norm,
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    url=item.get("url", ""),
                    rank=i,
                    rank_norm=float(r_norm),
                )
            )

    # Merge and sort by score desc
    merged: List[HybridDocEntry | HybridWebEntry] = [
        *doc_entries,
        *web_entries,
    ]
    merged.sort(key=lambda x: float(x["score"]), reverse=True)
    return merged
