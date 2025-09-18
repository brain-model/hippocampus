from __future__ import annotations

import pytest


@pytest.fixture()
def sample_text() -> str:
    return "Line 1  \nLine 2\n\n"
