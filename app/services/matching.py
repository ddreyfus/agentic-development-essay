from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Dict, List

from app.repositories.document_repository import DocumentRepository
from app.services.audit import AuditLogger
from app.services.rationale import RationaleService
from app.services.search import SearchBackend


class MatchingService:
    def __init__(
        self,
        repository: DocumentRepository,
        search_backend: SearchBackend,
        rationale_service: RationaleService,
        audit_logger: AuditLogger,
        client_id: int = 1,
    ) -> None:
        self._repository = repository
        self._search_backend = search_backend
        self._rationale_service = rationale_service
        self._audit_logger = audit_logger
        self._client_id = client_id

    def match(self, query: str) -> Dict[str, object]:
        results = self._search_backend.search(query, limit=2, client_id=self._client_id)
        candidate_ids = [doc_id for doc_id, _ in results]
        documents = self._repository.get_documents_by_ids(self._client_id, candidate_ids)
        document_by_id = {doc["id"]: doc for doc in documents}

        candidates: List[Dict[str, object]] = []
        for doc_id, score in results:
            doc = document_by_id.get(doc_id)
            if not doc:
                continue
            candidates.append(
                {
                    "document_id": doc_id,
                    "document_name": doc["document_name"],
                    "k_number": doc["k_number"],
                    "manufacturer_name": doc["manufacturer_name"],
                    "score": round(score, 4),
                    "rationale": self._rationale_service.generate(query, doc),
                }
            )

        created_at = datetime.now(timezone.utc).isoformat()
        match_id = self._repository.insert_match(query, candidate_ids, created_at)
        self._audit_logger.log(
            "SEARCH",
            match_id=match_id,
            payload={"candidate_ids": candidate_ids},
        )
        return {"match_id": match_id, "candidates": candidates}

    def confirm_match(self, match_id: int, selected_document_id: int) -> Dict[str, object]:
        self._repository.update_match_selection(match_id, selected_document_id)
        match = self._repository.get_match(match_id)
        if not match:
            raise ValueError("Match not found")
        candidate_ids = json.loads(match.get("candidate_document_ids_json") or "[]")
        self._audit_logger.log(
            "SELECT",
            match_id=match_id,
            document_id=selected_document_id,
            payload={"selected_document_id": selected_document_id, "candidate_ids": candidate_ids},
        )
        return {
            "id": match_id,
            "query_text": match["query_text"],
            "selected_document_id": selected_document_id,
            "candidate_document_ids": candidate_ids,
            "created_at": match["created_at"],
        }
