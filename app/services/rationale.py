from __future__ import annotations

from typing import Dict


class RationaleService:
    def generate(self, query: str, document: Dict[str, str]) -> str:
        document_type = document.get("document_type") or "document"
        return f"Shares terms with the query and the {document_type.lower()} text."
