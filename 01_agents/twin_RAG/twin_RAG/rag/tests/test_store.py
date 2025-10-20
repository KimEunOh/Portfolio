import numpy as np
from ragcore import NumpyFileVectorStore
from pathlib import Path


def test_numpy_store_add_and_search(tmp_path: Path):
    store = NumpyFileVectorStore(tmp_path / "vecs.npz")
    # 3 vectors at (1,0), (0,1), (-1,0)
    embs = np.array([[1, 0], [0, 1], [-1, 0]], dtype=np.float32)
    metas = [{"id": i} for i in range(3)]
    store.add(embs, metas)

    q = np.array([[1, 0]], dtype=np.float32)
    result = store.search(q, top_k=2)[0]
    assert result[0][0] == 0  # nearest (1,0)
    assert result[1][0] in (1, 2)
