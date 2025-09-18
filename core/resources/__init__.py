from __future__ import annotations

from pathlib import Path

"""Static resources for Hippocampus (prompts, templates, schemas).

Exposes constants and utilities to deterministically locate artifacts on disk.
"""

MANIFEST_SCHEMA_PATH: str = str(
    Path(__file__).resolve().parent / "schemas" / "manifest.schema.json"
)
