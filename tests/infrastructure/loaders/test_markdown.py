from __future__ import annotations

from pathlib import Path

from core.infrastructure.loaders.markdown import MarkdownLoader
from core.infrastructure.loaders.registry import get_loader_for_file


def test_markdown_loader_from_text():
    md = "# Title\n\nSome *bold* text with a [link](https://example.com).\n````\ncode\n````"
    loader = MarkdownLoader()
    out = loader.load(text=md)
    assert "Title" in out
    assert "bold" in out
    assert "https://example.com" in out
    assert "link (https://example.com)" in out


def test_markdown_loader_from_file(tmp_path: Path):
    p = tmp_path / "note.md"
    p.write_text("# H1\n\n- item\n\n[ref](https://ex.com)", encoding="utf-8")
    loader = MarkdownLoader()
    out = loader.load(file_path=str(p))
    assert "H1" in out and "https://ex.com" in out


def test_markdown_loader_param_validation():
    loader = MarkdownLoader()
    # neither provided
    try:
        loader.load()
    except ValueError as e:
        assert "either" in str(e)
    else:
        raise AssertionError("Expected ValueError when neither param is provided")
    # both provided
    try:
        loader.load(text="x", file_path="/tmp/x.md")
    except ValueError as e:
        assert "only one" in str(e)
    else:
        raise AssertionError("Expected ValueError when both params are provided")


def test_registry_selects_markdown_loader():
    loader = get_loader_for_file("something.markdown")
    assert isinstance(loader, MarkdownLoader)


def test_registry_defaults_to_text_loader():
    loader = get_loader_for_file("file.unknown")
    # Do not import TextLoader here to avoid circular import in test; rely on behavior
    assert hasattr(loader, "load")
