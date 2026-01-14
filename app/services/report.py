from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape


class ReportService:
    def __init__(self, templates_path: str) -> None:
        env = Environment(
            loader=FileSystemLoader(templates_path),
            autoescape=select_autoescape(),
        )
        self._template = env.get_template("report.md.j2")

    def render(self, match: Dict[str, str], document: Dict[str, str]) -> Dict[str, str]:
        created_at = datetime.now(timezone.utc).isoformat()
        markdown = self._template.render(match=match, document=document)
        return {"markdown": markdown, "created_at": created_at}
