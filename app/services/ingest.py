from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from app.repositories.document_repository import DocumentRepository
from app.services.audit import AuditLogger
from app.services.extraction import ExtractionService


class PdfIngestService:
    def __init__(
        self,
        repository: DocumentRepository,
        extraction_service: ExtractionService,
        audit_logger: AuditLogger,
        pdf_dir: str,
        client_id: int = 1,
    ) -> None:
        self._repository = repository
        self._extraction_service = extraction_service
        self._audit_logger = audit_logger
        self._pdf_dir = pdf_dir
        self._client_id = client_id

    def ingest_all(self) -> None:
        for pdf_path in self._list_pdfs():
            self.ingest_file(pdf_path)

    def ingest_file(self, pdf_path: Path) -> None:
        file_path = str(pdf_path)
        last_modified = datetime.fromtimestamp(os.path.getmtime(pdf_path), tz=timezone.utc).isoformat()
        existing = self._repository.get_pdf_file(self._client_id, file_path)
        if existing and existing.last_modified >= last_modified:
            return

        extraction = self._extraction_service.extract(pdf_path)
        now = datetime.now(timezone.utc).isoformat()
        version = 1 if not existing else existing.version + 1
        document_values = {
            "client_id": self._client_id,
            "k_number": extraction.fields["k_number"],
            "document_name": extraction.fields["document_name"],
            "document_type": extraction.fields.get("document_type") or extraction.fields["document_name"],
            "manufacturer_name": extraction.fields["manufacturer_name"],
            "manufacturer_address": extraction.fields.get("manufacturer_address") or "Unknown",
            "regulation_number": extraction.fields["regulation_number"],
            "regulation_name": extraction.fields["regulation_name"],
            "regulatory_class": extraction.fields["regulatory_class"],
            "product_codes": extraction.fields["product_codes"],
            "indications_for_use": extraction.fields["indications_for_use"],
            "version": version,
            "created_at": now,
            "updated_at": now,
            "full_text": extraction.full_text,
        }
        document_id = self._repository.insert_document_version(document_values)
        self._repository.upsert_pdf_file_pointer(
            self._client_id, file_path, last_modified, document_id, version
        )
        self._audit_logger.log("INGEST", document_id=document_id, payload={"file_path": file_path})

    def _list_pdfs(self) -> List[Path]:
        pdf_dir = Path(self._pdf_dir)
        if not pdf_dir.exists():
            return []
        return sorted([path for path in pdf_dir.rglob("*.pdf") if path.is_file()])
