from __future__ import annotations

import time
import sqlite3
from pathlib import Path

import requests


def wait_for_document_count(host_port: int, expected: int, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    url = f"http://localhost:{host_port}/documents"
    while time.time() < deadline:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("total") == expected:
            return
        time.sleep(0.5)
    raise RuntimeError(f"Document count did not reach {expected}")


def read_tables(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    conn.close()
    return {row[0] for row in rows}


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
