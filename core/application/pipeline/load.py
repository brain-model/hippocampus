"""Document loading and normalization module.

This module handles loading and normalizing documents from various sources:
- Text content directly
- Files via loader registry (text, markdown, PDF, LaTeX)
- Content normalization and preprocessing
"""

from __future__ import annotations

from pathlib import Path

from core.infrastructure.loaders.registry import get_loader_for_file
from core.infrastructure.loaders.text import TextLoader


def load_text_content(text: str) -> str:
    """Load and normalize text content.

    Args:
        text: Raw text content to load and normalize

    Returns:
        Normalized text content
    """
    loader = TextLoader()
    return loader.load(text=text)


def load_file_content(file_path: str) -> str:
    """Load and normalize content from a file.

    Args:
        file_path: Path to the file to load

    Returns:
        Normalized text content from the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If no loader is available for the file type
    """
    path = Path(file_path)
    if not path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)

    loader = get_loader_for_file(file_path)
    return loader.load(file_path=file_path)
