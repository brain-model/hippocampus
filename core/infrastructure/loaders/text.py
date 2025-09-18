"""Infrastructure loader for reading and normalizing textual content.

Supports both in-memory strings and filesystem paths with lightweight
normalization suitable for downstream extraction.
"""

from __future__ import annotations

from pathlib import Path


class TextLoader:
    """Simple text loader with normalization.

    Supports reading from in-memory string or file on disk, with basic
    whitespace normalization and trailing EOL cleanup.
    """

    def load(self, *, text: str | None = None, file_path: str | None = None) -> str:
        """Load text from memory or file and normalize it.

        Args:
            text: Text content. When provided, `file_path` must be None.
            file_path: File path. When provided, `text` must be None.

        Returns:
            Normalized text ready for processing.
        """
        if text is None and file_path is None:
            raise ValueError("Provide either text or file_path")
        if text is not None and file_path is not None:
            raise ValueError("Provide only one of text or file_path")
        if text is not None:
            return _normalize_text(text)
        p = Path(file_path).expanduser().resolve()
        data = p.read_text(encoding="utf-8", errors="ignore")
        return _normalize_text(data)


def _normalize_text(s: str) -> str:
    """Trim trailing spaces and normalize line breaks.

    Args:
        s: Raw input text.

    Returns:
        Text with trailing spaces removed from each line and no trailing blank lines.
    """
    return "\n".join(line.rstrip() for line in s.splitlines()).strip()
