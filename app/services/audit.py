from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.repositories.document_repository import DocumentRepository


class AuditLogger:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def log(
        self,
        event_type: str,
        document_id: Optional[int] = None,
        match_id: Optional[int] = None,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload or {})
        self._repository.insert_audit_event(event_type, timestamp, document_id, match_id, payload_json)
