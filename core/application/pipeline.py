"""Application pipeline for building and validating manifests.

This module orchestrates the MVP pipeline:
- Normalizes input text via `TextLoader`.
- Extracts heuristic references via `HeuristicExtractionAgent`.
- Assembles a minimal manifest dictionary with metadata.
- Validates against the JSON Schema at `MANIFEST_SCHEMA_PATH`.
- Persists the result as JSON in `out_dir/manifest/manifest.json`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from core.domain.manifest import MANIFEST_VERSION, STATUS_AWAITING
from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent
from core.infrastructure.formatters.json_writer import ManifestJsonWriter
from core.infrastructure.loaders.text import TextLoader
from core.resources import MANIFEST_SCHEMA_PATH

from .validation import validate_manifest


def build_manifest_from_text(text: str, out_dir: str) -> Dict[str, Any]:
    """Build and persist a manifest from input text.

    The flow loads and normalizes the text, extracts references, assembles
    the manifest dictionary, validates it against the JSON Schema, and writes
    the resulting JSON file to disk.

    Args:
        text: Input content to be indexed and analyzed.
        out_dir: Base directory where the JSON will be saved (subfolder `manifest`).

    Returns:
        The validated manifest dictionary persisted on disk.

    Raises:
        ValueError: If schema validation fails.
        OSError: If directory creation or file writing fails.
    """
    loader = TextLoader()
    extractor = HeuristicExtractionAgent()
    writer = ManifestJsonWriter()

    normalized = loader.load(text=text)
    extracted = extractor.extract(normalized)

    manifest: Dict[str, Any] = {
        "manifestVersion": MANIFEST_VERSION,
        "status": STATUS_AWAITING,
        "sourceDocument": {
            "sourceType": "text",
            "source": normalized[:5000],
            "sourceFormat": "text",
        },
        "knowledgeIndex": {
            "references": extracted.get("references", []),
        },
    }

    manifest["manifestId"] = uuid4().hex
    manifest["processedAt"] = datetime.now(timezone.utc).isoformat()

    validate_manifest(manifest, MANIFEST_SCHEMA_PATH)
    writer.write(manifest, out_dir)
    return manifest
