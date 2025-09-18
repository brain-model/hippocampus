from __future__ import annotations

import pytest


@pytest.fixture()
def argv_ok() -> list[str]:
    return ["-t", "Hello https://example.com", "-o", "./.tmp-out"]
