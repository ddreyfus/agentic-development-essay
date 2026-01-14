from __future__ import annotations

from typing import Dict

from app.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, repository: DocumentRepository, client_id: int = 1) -> None:
        self._repository = repository
        self._client_id = client_id

    def list_documents(self, limit: int, offset: int) -> Dict[str, object]:
        items = self._repository.list_documents(self._client_id, limit=limit, offset=offset)
        total = self._repository.count_documents(self._client_id)
        return {"items": items, "total": total}

    def get_document(self, document_id: int) -> Dict[str, object]:
        doc = self._repository.get_document(self._client_id, document_id)
        if not doc:
            raise ValueError("Document not found")
        full_text = doc.get("full_text", "")
        doc["full_text_excerpt"] = full_text[:400]
        return doc
