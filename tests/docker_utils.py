from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests


@dataclass
class ContainerHandle:
    container_id: str
    name: str
    host_port: int
    data_dir: Path


IMAGE_NAME = "document-matcher"


def get_free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return int(sock.getsockname()[1])


def build_image() -> None:
    subprocess.run(["docker", "build", "-t", IMAGE_NAME, "."], check=True)


def run_container(pdfs_dir: Path, data_dir: Path, host_port: int | None = None) -> ContainerHandle:
    if host_port is None:
        host_port = get_free_port()
    name = f"document-matcher-test-{uuid.uuid4().hex[:8]}"
    cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        name,
        "-p",
        f"{host_port}:8000",
        "-v",
        f"{pdfs_dir}:/pdfs",
        "-v",
        f"{data_dir}:/data",
        "-e",
        "DB_PATH=/data/document_matcher.db",
        IMAGE_NAME,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    container_id = result.stdout.strip()
    return ContainerHandle(container_id=container_id, name=name, host_port=host_port, data_dir=data_dir)


def stop_container(handle: ContainerHandle) -> None:
    subprocess.run(["docker", "stop", handle.name], check=False)


def wait_for_health(host_port: int, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    url = f"http://localhost:{host_port}/health"
    last_error: Optional[str] = None
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return
            last_error = f"status {response.status_code}"
        except Exception as exc:  # noqa: BLE001 - test helper
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"Container did not become healthy: {last_error}")


def read_db_rows(db_path: Path, table: str) -> list[dict[str, object]]:
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    conn.close()
    return [dict(row) for row in rows]
