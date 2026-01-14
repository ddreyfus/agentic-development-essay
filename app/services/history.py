from __future__ import annotations

import json
from typing import Dict, List

from app.repositories.document_repository import DocumentRepository


class MatchHistoryService:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def list_matches(self, limit: int, offset: int) -> Dict[str, object]:
        rows = self._repository.list_matches(limit=limit, offset=offset)
        items: List[Dict[str, object]] = []
        for row in rows:
            items.append(
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "query_text": row["query_text"],
                    "selected_document_id": row.get("selected_document_id"),
                    "selected_document_name": row.get("selected_document_name"),
                    "selected_document_k_number": row.get("selected_document_k_number"),
                    "report_generated": row.get("selected_document_id") is not None,
                }
            )
        total = self._repository.count_matches()
        return {"items": items, "total": total}

    def get_candidate_ids(self, match_id: int) -> List[int]:
        match = self._repository.get_match(match_id)
        if not match:
            return []
        return json.loads(match.get("candidate_document_ids_json") or "[]")
