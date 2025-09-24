"""Infrastructure loader for Markdown files with light normalization.

Provides a minimal Markdown-to-text conversion suitable for heuristic
extraction. Avoids external dependencies and focuses on stripping common
syntax while preserving readable text and URLs.
"""

from __future__ import annotations

import re
from pathlib import Path


class MarkdownLoader:
    """Simple Markdown loader that returns normalized plain text."""

    LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    CODE_FENCE_RE = re.compile(r"^```.*$", re.MULTILINE)
    HEADER_RE = re.compile(r"^#{1,6}\s*", re.MULTILINE)

    def load(self, *, text: str | None = None, file_path: str | None = None) -> str:
        """Load Markdown from memory or file and normalize it.

        Args:
            text: Markdown content. When provided, `file_path` must be None.
            file_path: File path. When provided, `text` must be None.

        Returns:
            A lightly de-markdowned, normalized text.
        """
        if text is None and file_path is None:
            raise ValueError("Provide either text or file_path")
        if text is not None and file_path is not None:
            raise ValueError("Provide only one of text or file_path")
        if text is None:
            p = Path(file_path).expanduser().resolve()
            text = p.read_text(encoding="utf-8", errors="ignore")

        txt = self._demarkdown(text)
        return self._normalize(txt)

    def _demarkdown(self, s: str) -> str:
        s = self.CODE_FENCE_RE.sub("", s)
        s = self.HEADER_RE.sub("", s)
        s = self.LINK_RE.sub(r"\1 (\2)", s)
        return s.replace("*", "").replace("_", "")

    def _normalize(self, s: str) -> str:
        return "\n".join(line.rstrip() for line in s.splitlines()).strip()
