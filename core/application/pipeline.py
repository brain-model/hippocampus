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
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from core.domain.manifest import MANIFEST_VERSION, STATUS_AWAITING
from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent
from core.infrastructure.formatters.json_writer import ManifestJsonWriter
from core.infrastructure.loaders.registry import get_loader_for_file
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


def build_manifest_from_file(file_path: str, out_dir: str) -> Dict[str, Any]:
    """Build and persist a manifest from an input file.

    Selects an appropriate loader based on the file extension, normalizes
    the content, extracts references, assembles the manifest, validates it
    and writes the resulting JSON file to disk.

    Args:
        file_path: Path to the input file.
        out_dir: Base directory where the JSON will be saved.

    Returns:
        The validated manifest dictionary persisted on disk.

    Raises:
        ValueError: If schema validation fails.
        OSError: If file reading or writing fails.
    """
    loader = get_loader_for_file(file_path)
    extractor = HeuristicExtractionAgent()
    writer = ManifestJsonWriter()

    normalized = loader.load(file_path=file_path)
    extracted = extractor.extract(normalized)

    manifest: Dict[str, Any] = {
        "manifestVersion": MANIFEST_VERSION,
        "status": STATUS_AWAITING,
        "sourceDocument": {
            "sourceType": "file",
            "source": normalized[:5000],
            "sourceFormat": Path(file_path).suffix.lstrip(".") or "file",
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
