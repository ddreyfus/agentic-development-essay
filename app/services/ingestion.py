"""PDF ingestion and extraction service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from app.db import utc_now

WORD_PATTERN = re.compile(r"\b\w+\b")


@dataclass(frozen=True)
class ExtractedDocument:
    """Structured representation of an ingested PDF."""

    filename: str
    title: str
    content: str
    summary: str
    page_count: int
    word_count: int
    created_at: str


def ingest_pdfs(pdf_dir: Path) -> Iterable[ExtractedDocument]:
    """Extract text and metadata from PDFs in the given directory."""
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        text_chunks = [(page.extract_text() or "").strip() for page in reader.pages]
        content = "\n".join(chunk for chunk in text_chunks if chunk)
        content = content.strip()
        title = _extract_title(content, pdf_path.stem)
        summary = _extract_summary(content)
        word_count = len(WORD_PATTERN.findall(content))
        yield ExtractedDocument(
            filename=pdf_path.name,
            title=title,
            content=content,
            summary=summary,
            page_count=len(reader.pages),
            word_count=word_count,
            created_at=utc_now(),
        )


def _extract_title(content: str, fallback: str) -> str:
    """Use the first non-empty line as a title, fallback to filename stem."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return fallback


def _extract_summary(content: str) -> str:
    """Create a brief summary snippet for display."""
    if not content:
        return "(No extractable text found.)"
    snippet = " ".join(content.split())
    return snippet[:360] + ("..." if len(snippet) > 360 else "")
