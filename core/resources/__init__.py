from __future__ import annotations

from pathlib import Path

# Caminho absoluto fixo para o schema de manifesto
MANIFEST_SCHEMA_PATH: str = str(
    Path(__file__).resolve().parent / "schemas" / "manifest.schema.json"
)
