from __future__ import annotations
from dataclasses import dataclass
from typing import List, Sequence
import numpy as np


class BaseEmbedder:
    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:  # (n, d)
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        raise NotImplementedError


@dataclass
class FakeEmbedder(BaseEmbedder):
    dim: int = 8
    seed: int = 42

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.seed)

    @property
    def dimension(self) -> int:
        return self.dim

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        # Deterministic per text using hash seed
        vectors: List[np.ndarray] = []
        for t in texts:
            h = abs(hash(t)) % (2**32)
            rng = np.random.default_rng(h)
            v = rng.standard_normal(self.dim, dtype=np.float32)
            # Normalize for cosine
            norm = np.linalg.norm(v) + 1e-9
            vectors.append((v / norm).astype(np.float32))
        return (
            np.stack(vectors, axis=0)
            if vectors
            else np.zeros((0, self.dim), dtype=np.float32)
        )


class SbertModelNotAvailable(RuntimeError):
    pass


class SbertEmbedder(BaseEmbedder):
    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:  # pragma: no cover - runtime only
            raise SbertModelNotAvailable(
                "sentence-transformers is not installed"
            ) from e
        self._model = SentenceTransformer(model_name)
        # Infer dimension lazily
        emb = self._model.encode(
            ["test"], convert_to_numpy=True, normalize_embeddings=True
        )
        self._dim = int(emb.shape[1])

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: Sequence[str]) -> np.ndarray:
        arr = self._model.encode(
            list(texts), convert_to_numpy=True, normalize_embeddings=True
        )
        return arr.astype(np.float32)
