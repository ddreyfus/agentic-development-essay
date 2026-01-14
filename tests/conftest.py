"""Shared pytest fixtures for API tests."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Generator, Tuple

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import db as db_module  # noqa: E402
from app.main import app, get_pdf_dir, get_report_dir  # noqa: E402


@pytest.fixture()
def client(tmp_path: Path) -> Generator[Tuple[TestClient, Path], None, None]:
    """Provide a test client backed by a temp sqlite db and report directory."""
    db_module.DB_PATH = tmp_path / "test.db"
    db_module.init_db()

    pdf_dir = Path(__file__).resolve().parents[1] / "pdfs"
    report_dir = tmp_path / "reports"

    app.dependency_overrides[get_pdf_dir] = lambda: pdf_dir
    app.dependency_overrides[get_report_dir] = lambda: report_dir

    with TestClient(app) as test_client:
        yield test_client, report_dir

    app.dependency_overrides.clear()
