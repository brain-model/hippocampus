"""File I/O and path management module.

This module handles file operations and path management for the pipeline:
- Manifest JSON writing to disk
- Directory creation and path handling
- File I/O error handling
"""

from __future__ import annotations

from typing import Any

from core.infrastructure.formatters.json_writer import ManifestJsonWriter


def write_manifest(manifest: dict[str, Any], out_dir: str) -> None:
    """Write manifest dictionary to JSON file on disk.

    Args:
        manifest: The manifest dictionary to write
        out_dir: Base directory where manifest/manifest.json will be created

    Raises:
        OSError: If directory creation or file writing fails
    """
    writer = ManifestJsonWriter()
    writer.write(manifest, out_dir)
