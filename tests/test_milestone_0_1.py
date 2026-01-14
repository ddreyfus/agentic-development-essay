from __future__ import annotations

from pathlib import Path

import requests

from tests.docker_utils import run_container, stop_container, wait_for_health


def test_container_build_and_health(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    handle = run_container(Path("pdfs").resolve(), data_dir)
    try:
        wait_for_health(handle.host_port)
        response = requests.get(f"http://localhost:{handle.host_port}/health", timeout=5)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    finally:
        stop_container(handle)


def test_static_frontend_served(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    handle = run_container(Path("pdfs").resolve(), data_dir, host_port=8002)
    try:
        wait_for_health(handle.host_port)
        response = requests.get(f"http://localhost:{handle.host_port}/", timeout=5)
        assert response.status_code == 200
        assert "<div id=\"root\"></div>" in response.text
    finally:
        stop_container(handle)
