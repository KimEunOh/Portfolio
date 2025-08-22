from pathlib import Path
from typing import Union

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover - optional dependency at runtime
    PdfReader = None  # type: ignore

PathLike = Union[str, Path]


def read_markdown(path: PathLike) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8")


def read_pdf(path: PathLike) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed; cannot read PDFs")
    p = Path(path)
    reader = PdfReader(str(p))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)
