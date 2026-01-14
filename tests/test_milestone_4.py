from __future__ import annotations

import shutil
from pathlib import Path

import requests

from tests.docker_utils import get_free_port, run_container, stop_container, wait_for_health
from tests.helpers import connect_db, wait_for_document_count


def test_pdf_extraction_deterministic(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    pdf_dir = tmp_path / "pdfs"
    data_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    sample_pdf = Path("pdfs/K240666.pdf")
    shutil.copy(sample_pdf, pdf_dir / sample_pdf.name)

    handle = run_container(pdf_dir, data_dir, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        wait_for_document_count(handle.host_port, 1)
        db_path = data_dir / "document_matcher.db"
        conn = connect_db(db_path)
        row = conn.execute("SELECT * FROM documents").fetchone()
        conn.close()
        assert row["full_text"]
        fields_snapshot = dict(row)
    finally:
        stop_container(handle)

    data_dir_2 = tmp_path / "data2"
    data_dir_2.mkdir(parents=True, exist_ok=True)
    handle = run_container(pdf_dir, data_dir_2, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        wait_for_document_count(handle.host_port, 1)
        db_path = data_dir_2 / "document_matcher.db"
        conn = connect_db(db_path)
        row = conn.execute("SELECT * FROM documents").fetchone()
        conn.close()
        assert row["full_text"] == fields_snapshot["full_text"]
        for field in [
            "k_number",
            "document_name",
            "regulation_number",
            "regulation_name",
            "regulatory_class",
            "product_codes",
            "manufacturer_name",
        ]:
            assert row[field] == fields_snapshot[field]
    finally:
        stop_container(handle)


def test_all_sample_pdfs_parse_and_are_complete_via_api(tmp_path: Path) -> None:
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
        for item in items:
            doc_id = item["id"]
            doc_response = requests.get(
                f"http://localhost:{handle.host_port}/documents/{doc_id}", timeout=5
            )
            doc_response.raise_for_status()
            doc = doc_response.json()
            for key in [
                "k_number",
                "document_name",
                "document_type",
                "manufacturer_name",
                "regulation_number",
                "regulation_name",
                "regulatory_class",
                "product_codes",
                "indications_for_use",
                "full_text_excerpt",
            ]:
                assert doc.get(key)
    finally:
        stop_container(handle)
