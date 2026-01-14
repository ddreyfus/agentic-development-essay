from __future__ import annotations

from typing import Dict

from app.repositories.document_repository import DocumentRepository


class UserService:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def current_user(self) -> Dict[str, str]:
        identity = self._repository.get_demo_identity()
        return {
            "client_name": identity["client_name"],
            "user_name": identity.get("user_name", "demo"),
            "user_email": identity["user_email"],
            "user_role": identity["user_role"],
        }
