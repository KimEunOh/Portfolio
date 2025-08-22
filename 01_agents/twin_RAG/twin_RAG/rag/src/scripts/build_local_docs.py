from __future__ import annotations

import argparse
import os
from pathlib import Path

from ragcore.embedder import FakeEmbedder
from ragcore.pipeline import build_embeddings_for_documents
from ragcore.store import NumpyFileVectorStore


def read_text_files(root: Path) -> list[str]:
    docs: list[str] = []
    for ext in ("*.md", "*.txt"):
        for p in root.rglob(ext):
            try:
                text = p.read_text(encoding="utf-8")
                docs.append(text)
            except Exception:
                # Skip unreadable files
                continue
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local vector store from docs")
    parser.add_argument(
        "docs_dir",
        nargs="?",
        default=str(Path(__file__).resolve().parents[2] / "data" / "docs"),
        help="Directory containing .md/.txt documents",
    )
    parser.add_argument(
        "--store-path",
        dest="store_path",
        default=os.getenv(
            "RAG_STORE_PATH",
            str(Path(__file__).resolve().parents[2] / "data" / "vectors.npz"),
        ),
        help="Path to vectors.npz store (defaults to RAG_STORE_PATH or data/vectors.npz)",
    )
    args = parser.parse_args()

    docs = read_text_files(Path(args.docs_dir))
    if not docs:
        print("No documents found. Provide a directory with .md/.txt files.")
        return

    store = NumpyFileVectorStore(args.store_path)
    embedder = FakeEmbedder(dim=8)
    n = build_embeddings_for_documents(docs, embedder, store)
    print(f"Built {n} chunks into store: {args.store_path}")


if __name__ == "__main__":
    main()
