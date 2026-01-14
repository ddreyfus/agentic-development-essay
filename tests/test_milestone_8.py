from __future__ import annotations

import shutil
from pathlib import Path

import requests

from tests.docker_utils import get_free_port, run_container, stop_container, wait_for_health
from tests.helpers import connect_db, wait_for_document_count


def test_report_generation(tmp_path: Path) -> None:
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
        selected_id = body["candidates"][0]["document_id"]
        response = requests.put(
            f"http://localhost:{handle.host_port}/matches/{body['match_id']}",
            json={"selected_document_id": selected_id},
            timeout=10,
        )
        response.raise_for_status()

        response = requests.get(
            f"http://localhost:{handle.host_port}/matches/{body['match_id']}/report", timeout=10
        )
        response.raise_for_status()
        report = response.json()
        assert "Document Match Report" in report["markdown"]

        db_path = data_dir / "document_matcher.db"
        conn = connect_db(db_path)
        audit_row = conn.execute(
            "SELECT * FROM audit_events WHERE event_type = 'REPORT_GENERATED' AND match_id = ?",
            (body["match_id"],),
        ).fetchone()
        conn.close()
        assert audit_row is not None
    finally:
        stop_container(handle)
