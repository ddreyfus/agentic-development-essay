"""Database helpers for sqlite persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DB_PATH = Path("data/app.db")


def get_connection() -> sqlite3.Connection:
    """Return a sqlite connection with row factory enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                word_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def utc_now() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def insert_audit_event(event_type: str, details: dict[str, Any]) -> None:
    """Persist an audit event with structured details."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_events (event_type, details, created_at)
            VALUES (?, ?, ?)
            """,
            (event_type, json.dumps(details), utc_now()),
        )
        connection.commit()


def fetch_all_audits() -> list[sqlite3.Row]:
    """Fetch all audit events in reverse chronological order."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, event_type, details, created_at
            FROM audit_events
            ORDER BY id DESC
            """
        )
        return list(cursor.fetchall())


def insert_documents(records: Iterable[dict[str, Any]]) -> int:
    """Insert multiple document records and return inserted count."""
    record_list = list(records)
    if not record_list:
        return 0
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO documents (
                filename, title, content, summary, page_count, word_count, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    record["filename"],
                    record["title"],
                    record["content"],
                    record["summary"],
                    record["page_count"],
                    record["word_count"],
                    record["created_at"],
                )
                for record in record_list
            ],
        )
        connection.commit()
        return len(record_list)


def clear_documents() -> None:
    """Remove existing documents (used before fresh ingest)."""
    with get_connection() as connection:
        connection.execute("DELETE FROM documents")
        connection.commit()


def fetch_documents() -> list[sqlite3.Row]:
    """Fetch all documents in insertion order."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, filename, title, content, summary, page_count, word_count, created_at
            FROM documents
            ORDER BY id ASC
            """
        )
        return list(cursor.fetchall())


def fetch_document(document_id: int) -> sqlite3.Row | None:
    """Fetch a single document by id."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, filename, title, content, summary, page_count, word_count, created_at
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        )
        return cursor.fetchone()


def insert_selection(document_id: int) -> dict[str, object]:
    """Persist a confirmed selection."""
    created_at = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO selections (document_id, created_at)
            VALUES (?, ?)
            """,
            (document_id, created_at),
        )
        selection_id = cursor.lastrowid
        connection.commit()
    return {
        "id": selection_id,
        "document_id": document_id,
        "created_at": created_at,
    }
