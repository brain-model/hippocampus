from __future__ import annotations

from pathlib import Path

import pytest

from core.infrastructure.loaders.text import TextLoader, _normalize_text


def test_normalize_text(sample_text: str):
    assert _normalize_text(sample_text) == "Line 1\nLine 2"


def test_load_text_inline(sample_text: str):
    loader = TextLoader()
    assert loader.load(text=sample_text) == "Line 1\nLine 2"


def test_load_text_from_file(tmp_path: Path):
    p = tmp_path / "f.txt"
    p.write_text("A  \nB\n\n", encoding="utf-8")
    loader = TextLoader()
    assert loader.load(file_path=str(p)) == "A\nB"


@pytest.mark.parametrize("text,file_path", [(None, None), ("x", "y")])
def test_load_invalid_args(text, file_path):
    loader = TextLoader()
    with pytest.raises(ValueError):
        loader.load(text=text, file_path=file_path)
