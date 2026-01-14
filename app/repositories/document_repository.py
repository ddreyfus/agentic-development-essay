from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class PdfFileRecord:
    id: int
    client_id: int
    file_path: str
    last_modified: str
    document_id: int
    version: int


class DocumentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_pdf_file(self, client_id: int, file_path: str) -> Optional[PdfFileRecord]:
        row = self._conn.execute(
            "SELECT * FROM pdf_files WHERE client_id = ? AND file_path = ?",
            (client_id, file_path),
        ).fetchone()
        if row is None:
            return None
        return PdfFileRecord(**dict(row))

    def insert_document_version(self, values: Dict[str, Any]) -> int:
        columns = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        sql = f"INSERT INTO documents ({columns}) VALUES ({placeholders})"
        cur = self._conn.execute(sql, tuple(values.values()))
        self._conn.commit()
        return int(cur.lastrowid)

    def upsert_pdf_file_pointer(
        self,
        client_id: int,
        file_path: str,
        last_modified: str,
        document_id: int,
        version: int,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO pdf_files (client_id, file_path, last_modified, document_id, version)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(client_id, file_path) DO UPDATE SET
              last_modified = excluded.last_modified,
              document_id = excluded.document_id,
              version = excluded.version
            """,
            (client_id, file_path, last_modified, document_id, version),
        )
        self._conn.commit()

    def list_documents(self, client_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT id, k_number, document_name, manufacturer_name, regulatory_class
            FROM documents
            WHERE client_id = ?
            ORDER BY id
            LIMIT ? OFFSET ?
            """,
            (client_id, limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def count_documents(self, client_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS count FROM documents WHERE client_id = ?",
            (client_id,),
        ).fetchone()
        return int(row["count"]) if row else 0

    def get_document(self, client_id: int, document_id: int) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM documents WHERE client_id = ? AND id = ?",
            (client_id, document_id),
        ).fetchone()
        return dict(row) if row else None

    def get_documents_by_ids(self, client_id: int, ids: Iterable[int]) -> List[Dict[str, Any]]:
        ids_list = list(ids)
        if not ids_list:
            return []
        placeholders = ",".join(["?"] * len(ids_list))
        rows = self._conn.execute(
            f"SELECT * FROM documents WHERE client_id = ? AND id IN ({placeholders})",
            (client_id, *ids_list),
        ).fetchall()
        return [dict(row) for row in rows]

    def insert_match(self, query_text: str, candidate_ids: List[int], created_at: str) -> int:
        payload = json.dumps(candidate_ids)
        cur = self._conn.execute(
            "INSERT INTO matches (query_text, selected_document_id, candidate_document_ids_json, created_at)"
            " VALUES (?, NULL, ?, ?)",
            (query_text, payload, created_at),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def update_match_selection(self, match_id: int, selected_document_id: int) -> None:
        self._conn.execute(
            "UPDATE matches SET selected_document_id = ? WHERE id = ?",
            (selected_document_id, match_id),
        )
        self._conn.commit()

    def get_match(self, match_id: int) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT * FROM matches WHERE id = ?",
            (match_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_matches(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT m.*, d.document_name AS selected_document_name, d.k_number AS selected_document_k_number
            FROM matches m
            LEFT JOIN documents d ON m.selected_document_id = d.id
            ORDER BY m.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def count_matches(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS count FROM matches").fetchone()
        return int(row["count"]) if row else 0

    def list_parsing_rules(self, client_id: int) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT field_name, pattern, priority
            FROM field_parsing_rules
            WHERE client_id = ?
            ORDER BY priority ASC
            """,
            (client_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def insert_audit_event(
        self,
        event_type: str,
        timestamp: str,
        document_id: Optional[int],
        match_id: Optional[int],
        payload_json: str,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO audit_events (event_type, timestamp, document_id, match_id, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_type, timestamp, document_id, match_id, payload_json),
        )
        self._conn.commit()

    def get_demo_identity(self) -> Dict[str, Any]:
        row = self._conn.execute(
            """
            SELECT c.name AS client_name, u.email AS user_email, u.role AS user_role
            FROM users u
            JOIN clients c ON u.client_id = c.id
            WHERE u.id = 1
            """
        ).fetchone()
        if row is None:
            return {
                "client_name": "DemoClient",
                "user_name": "demo",
                "user_email": "demo@client.com",
                "user_role": "editor",
            }
        data = dict(row)
        data["user_name"] = "demo"
        return data
