from __future__ import annotations

import shutil
from pathlib import Path

from tests.docker_utils import get_free_port, run_container, stop_container, wait_for_health
from tests.helpers import connect_db, wait_for_document_count


def test_runtime_watcher_ingest(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    pdf_dir = tmp_path / "pdfs"
    data_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    sample_pdfs = list(Path("pdfs").glob("*.pdf"))
    shutil.copy(sample_pdfs[0], pdf_dir / sample_pdfs[0].name)

    handle = run_container(pdf_dir, data_dir, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        wait_for_document_count(handle.host_port, 1)
        shutil.copy(sample_pdfs[1], pdf_dir / sample_pdfs[1].name)
        wait_for_document_count(handle.host_port, 2, timeout=40)

        db_path = data_dir / "document_matcher.db"
        conn = connect_db(db_path)
        audit_row = conn.execute(
            "SELECT * FROM audit_events WHERE event_type = 'INGEST' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert audit_row is not None
        assert audit_row["document_id"] is not None
    finally:
        stop_container(handle)
