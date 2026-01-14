from __future__ import annotations

import sqlite3
from typing import List, Tuple


class SearchBackend:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def search(self, query: str, limit: int, client_id: int) -> List[Tuple[int, float]]:
        rows = self._conn.execute(
            """
            SELECT d.id AS document_id, bm25(documents_fts) AS score
            FROM documents_fts
            JOIN documents d ON documents_fts.rowid = d.id
            WHERE documents_fts MATCH ? AND d.client_id = ?
            ORDER BY score ASC
            LIMIT ?
            """,
            (query, client_id, limit),
        ).fetchall()
        results: List[Tuple[int, float]] = []
        for row in rows:
            raw_score = float(row["score"])
            score = 1.0 / (1.0 + raw_score)
            results.append((int(row["document_id"]), score))
        return results
