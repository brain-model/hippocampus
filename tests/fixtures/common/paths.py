from __future__ import annotations

from pathlib import Path

import pytest

from core.resources import MANIFEST_SCHEMA_PATH


@pytest.fixture()
def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture()
def schema_path(project_root: Path) -> str:
    return MANIFEST_SCHEMA_PATH


@pytest.fixture()
def tmp_out_dir(tmp_path: Path) -> str:
    return str(tmp_path)
