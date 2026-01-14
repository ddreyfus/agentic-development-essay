from __future__ import annotations

import shutil
from pathlib import Path

import requests

from tests.docker_utils import get_free_port, run_container, stop_container, wait_for_health
from tests.helpers import connect_db, wait_for_document_count


def test_documents_and_search(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    pdf_dir = tmp_path / "pdfs"
    data_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    sample_pdfs = list(Path("pdfs").glob("*.pdf"))
    for pdf in sample_pdfs:
        shutil.copy(pdf, pdf_dir / pdf.name)

    handle = run_container(pdf_dir, data_dir, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        wait_for_document_count(handle.host_port, len(sample_pdfs))
        response = requests.get(f"http://localhost:{handle.host_port}/documents", timeout=5)
        response.raise_for_status()
        items = response.json()["items"]
        assert len(items) == len(sample_pdfs)

        db_path = data_dir / "document_matcher.db"
        conn = connect_db(db_path)
        rows = conn.execute(
            "SELECT rowid FROM documents_fts WHERE documents_fts MATCH ? ORDER BY bm25(documents_fts)",
            ("oxygenator",),
        ).fetchall()
        conn.close()
        assert rows
        first = [row[0] for row in rows]

        conn = connect_db(db_path)
        rows_repeat = conn.execute(
            "SELECT rowid FROM documents_fts WHERE documents_fts MATCH ? ORDER BY bm25(documents_fts)",
            ("oxygenator",),
        ).fetchall()
        conn.close()
        second = [row[0] for row in rows_repeat]
        assert first == second
    finally:
        stop_container(handle)
