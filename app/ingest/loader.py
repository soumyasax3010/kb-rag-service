"""Document loaders: extract plain text from PDF / Markdown / TXT.

Kept as small per-format functions behind one ``load_text`` dispatcher so
adding a format (docx, html, ...) is a one-liner here.
"""

from pathlib import Path

from pypdf import PdfReader


def _load_pdf(data: bytes) -> str:
    reader = PdfReader(__import__("io").BytesIO(data))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def _load_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def load_text(data: bytes, filename: str) -> str:
    """Return extracted text for the given file bytes + name."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(data)
    if suffix in {".md", ".markdown", ".txt"}:
        # Markdown is treated as plain text; chunking doesn't need structure here.
        return _load_text(data)
    raise ValueError(f"Unsupported file type: {suffix}")
