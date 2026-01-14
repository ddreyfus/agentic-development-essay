from __future__ import annotations

import shutil
import time
from pathlib import Path

import requests

from tests.docker_utils import get_free_port, run_container, stop_container, wait_for_health
from tests.helpers import wait_for_document_count


def test_startup_ingest_idempotent(tmp_path: Path) -> None:
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
    finally:
        stop_container(handle)

    handle = run_container(pdf_dir, data_dir, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        wait_for_document_count(handle.host_port, len(sample_pdfs))
    finally:
        stop_container(handle)

    modified_pdf = pdf_dir / sample_pdfs[0].name
    modified_pdf.touch()

    handle = run_container(pdf_dir, data_dir, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        wait_for_document_count(handle.host_port, len(sample_pdfs) + 1)
    finally:
        stop_container(handle)


def test_ingest_rescan_endpoint(tmp_path: Path) -> None:
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
        response = requests.post(f"http://localhost:{handle.host_port}/ingest/rescan", timeout=5)
        assert response.status_code == 202

        shutil.copy(sample_pdfs[1], pdf_dir / sample_pdfs[1].name)
        time.sleep(1)
        response = requests.post(f"http://localhost:{handle.host_port}/ingest/rescan", timeout=5)
        assert response.status_code == 202
        wait_for_document_count(handle.host_port, 2, timeout=60)
    finally:
        stop_container(handle)
