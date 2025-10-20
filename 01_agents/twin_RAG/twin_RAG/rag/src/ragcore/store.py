from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple
import numpy as np


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a_norm @ b_norm.T


@dataclass
class NumpyFileVectorStore:
    path: Path

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._embeddings: np.ndarray | None = None
        self._metadatas: List[dict] | None = None

    def add(self, embeddings: np.ndarray, metadatas: Sequence[dict]) -> None:
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        if len(metadatas) != embeddings.shape[0]:
            raise ValueError("metadatas length must match embeddings rows")
        if self._embeddings is None:
            self._embeddings = embeddings
            self._metadatas = list(metadatas)
        else:
            self._embeddings = np.vstack([self._embeddings, embeddings])
            assert self._metadatas is not None
            self._metadatas.extend(list(metadatas))
        np.savez_compressed(
            self.path,
            embeddings=self._embeddings,
            metadatas=np.array(self._metadatas, dtype=object),
        )

    def load(self) -> Tuple[np.ndarray, List[dict]]:
        if self._embeddings is not None and self._metadatas is not None:
            return self._embeddings, self._metadatas
        if not self.path.exists():
            return np.zeros((0, 0), dtype=np.float32), []
        data = np.load(self.path, allow_pickle=True)
        self._embeddings = data["embeddings"].astype(np.float32)
        self._metadatas = list(data["metadatas"].tolist())
        return self._embeddings, self._metadatas  # type: ignore

    def search(
        self, query_embeddings: np.ndarray, top_k: int = 5
    ) -> List[List[Tuple[int, float]]]:
        embeddings, _ = self.load()
        if embeddings.size == 0:
            return [[] for _ in range(query_embeddings.shape[0])]
        sims = _cosine_sim(query_embeddings, embeddings)
        results: List[List[Tuple[int, float]]] = []
        for i in range(sims.shape[0]):
            idx = np.argsort(-sims[i])[:top_k]
            results.append([(int(j), float(sims[i, j])) for j in idx])
        return results


class FaissVectorStore:
    def __init__(self, dim: int):
        try:
            import faiss  # type: ignore
        except Exception as e:  # pragma: no cover - optional
            raise RuntimeError("faiss is not installed") from e
        self._faiss = faiss
        self._index = faiss.IndexFlatIP(dim)
        self._dim = dim
        self._metadatas: List[dict] = []

    def add(self, embeddings: np.ndarray, metadatas: Sequence[dict]) -> None:
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        # Normalize to use inner product as cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9
        normalized = embeddings / norms
        self._index.add(normalized)
        self._metadatas.extend(list(metadatas))

    def search(
        self, query_embeddings: np.ndarray, top_k: int = 5
    ) -> List[List[Tuple[int, float]]]:
        if query_embeddings.dtype != np.float32:
            query_embeddings = query_embeddings.astype(np.float32)
        norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True) + 1e-9
        q = query_embeddings / norms
        sims, idxs = self._index.search(q, top_k)
        results: List[List[Tuple[int, float]]] = []
        for i in range(q.shape[0]):
            row: List[Tuple[int, float]] = []
            for j, score in zip(idxs[i], sims[i]):
                if j == -1:
                    continue
                row.append((int(j), float(score)))
            results.append(row)
        return results
