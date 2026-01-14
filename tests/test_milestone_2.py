from __future__ import annotations

from pathlib import Path

import requests

from tests.docker_utils import get_free_port, run_container, stop_container, wait_for_health
from tests.helpers import read_tables


def test_db_bootstrap(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    pdf_dir = tmp_path / "pdfs"
    data_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    handle = run_container(pdf_dir, data_dir, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        db_path = data_dir / "document_matcher.db"
        assert db_path.exists()
        tables = read_tables(db_path)
        for table in {
            "clients",
            "users",
            "documents",
            "document_attributes",
            "matches",
            "audit_events",
            "pdf_files",
            "field_parsing_rules",
            "documents_fts",
        }:
            assert table in tables
    finally:
        stop_container(handle)


def test_user_current_endpoint(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    pdf_dir = tmp_path / "pdfs"
    data_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    handle = run_container(pdf_dir, data_dir, host_port=get_free_port())
    try:
        wait_for_health(handle.host_port)
        response = requests.get(f"http://localhost:{handle.host_port}/user/current", timeout=5)
        response.raise_for_status()
        body = response.json()
        assert body["client_name"] == "DemoClient"
        assert body["user_email"] == "demo@client.com"
        assert body["user_role"] == "editor"
    finally:
        stop_container(handle)
