from __future__ import annotations

import pytest

from tests.docker_utils import build_image


@pytest.fixture(scope="session", autouse=True)
def docker_image() -> None:
    build_image()
