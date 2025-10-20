import numpy as np
from ragcore import FakeEmbedder


def test_fake_embedder_shapes_and_types():
    emb = FakeEmbedder(dim=16)
    vecs = emb.embed_texts(["a", "b", "c"])
    assert vecs.shape == (3, 16)
    assert vecs.dtype == np.float32
    # Cosine normalized approximately
    norms = np.linalg.norm(vecs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)
