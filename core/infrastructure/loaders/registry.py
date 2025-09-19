"""Loader registry for selecting the appropriate loader by file extension."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .latex import LatexLoader
from .markdown import MarkdownLoader
from .pdf import PdfLoader
from .text import TextLoader


class _Loader(Protocol):
    def load(self, *, text: str | None = None, file_path: str | None = None) -> str: ...


_REGISTRY: dict[str, type[_Loader]] = {
    ".txt": TextLoader,  # plain text
    ".md": MarkdownLoader,  # markdown
    ".markdown": MarkdownLoader,
    ".tex": LatexLoader,
    ".pdf": PdfLoader,
}


def get_loader_for_file(path: str) -> _Loader:
    """Return a loader instance based on file extension.

    Defaults to `TextLoader` when extension is unknown.
    """
    ext = Path(path).suffix.lower()
    cls = _REGISTRY.get(ext, TextLoader)
    return cls()
