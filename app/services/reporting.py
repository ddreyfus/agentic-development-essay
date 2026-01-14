from __future__ import annotations

from typing import Dict

from app.repositories.document_repository import DocumentRepository
from app.services.audit import AuditLogger
from app.services.report import ReportService


class ReportWorkflow:
    def __init__(
        self,
        repository: DocumentRepository,
        report_service: ReportService,
        audit_logger: AuditLogger,
        client_id: int = 1,
    ) -> None:
        self._repository = repository
        self._report_service = report_service
        self._audit_logger = audit_logger
        self._client_id = client_id

    def generate(self, match_id: int) -> Dict[str, str]:
        match = self._repository.get_match(match_id)
        if not match:
            raise ValueError("Match not found")
        selected_id = match.get("selected_document_id")
        if not selected_id:
            raise ValueError("Match has no selected document")
        document = self._repository.get_document(self._client_id, int(selected_id))
        if not document:
            raise ValueError("Document not found")
        report = self._report_service.render(match, document)
        self._audit_logger.log("REPORT_GENERATED", document_id=document["id"], match_id=match_id)
        return {"match_id": match_id, "markdown": report["markdown"], "created_at": report["created_at"]}
