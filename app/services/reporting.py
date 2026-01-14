"""Report generation service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Report:
    """Generated report data."""

    document_id: int
    report_path: str
    content: str


def generate_report(document: dict[str, object], output_dir: Path) -> Report:
    """Generate a markdown report for the confirmed document."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    report_path = output_dir / f"report_{document['id']}_{timestamp}.md"
    content = _render_report(document)
    report_path.write_text(content, encoding="utf-8")
    return Report(document_id=int(document["id"]), report_path=str(report_path), content=content)


def _render_report(document: dict[str, object]) -> str:
    """Render report content."""
    return (
        "# Document Match Report\n\n"
        f"**Document ID:** {document['id']}\n"
        f"**Filename:** {document['filename']}\n"
        f"**Title:** {document['title']}\n"
        f"**Pages:** {document['page_count']}\n"
        f"**Word Count:** {document['word_count']}\n"
        f"**Generated At:** {datetime.now(timezone.utc).isoformat()}\n\n"
        "## Summary\n"
        f"{document['summary']}\n\n"
        "## Excerpt\n"
        f"{str(document['content'])[:1500]}\n"
    )
