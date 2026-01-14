from __future__ import annotations

import json
import shutil
from pathlib import Path

import requests

from tests.docker_utils import get_free_port, run_container, stop_container, wait_for_health
from tests.helpers import connect_db, wait_for_document_count


def test_match_creation(tmp_path: Path) -> None:
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
        response = requests.post(
            f"http://localhost:{handle.host_port}/match",
            json={"query": "oxygenator with arterial filter"},
            timeout=10,
        )
        response.raise_for_status()
        body = response.json()
        assert len(body["candidates"]) == 2

        db_path = data_dir / "document_matcher.db"
        conn = connect_db(db_path)
        match_row = conn.execute("SELECT * FROM matches WHERE id = ?", (body["match_id"],)).fetchone()
        audit_row = conn.execute(
            "SELECT * FROM audit_events WHERE event_type = 'SEARCH' AND match_id = ?",
            (body["match_id"],),
        ).fetchone()
        conn.close()
        assert match_row is not None
        candidate_ids = json.loads(match_row["candidate_document_ids_json"])
        assert len(candidate_ids) == 2
        assert audit_row is not None
    finally:
        stop_container(handle)
