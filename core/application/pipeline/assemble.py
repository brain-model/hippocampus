"""Manifest assembly module.

This module handles the assembly of manifest dictionaries with proper metadata:
- manifestVersion, status, manifestId, processedAt
- sourceDocument structure
- knowledgeIndex with references
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from core.domain.manifest import MANIFEST_VERSION, STATUS_AWAITING


def assemble_manifest(
    normalized_content: str,
    extracted_refs: dict[str, Any],
    source_type: str = "text",
    source_format: str = "text",
) -> dict[str, Any]:
    """Assemble a manifest dictionary from normalized content and extracted references.

    Args:
        normalized_content: The normalized/processed content
        extracted_refs: Dictionary containing extracted references
        source_type: Type of the source document
        source_format: Format of the source document

    Returns:
        Complete manifest dictionary with metadata
    """
    manifest: dict[str, Any] = {
        "manifestVersion": MANIFEST_VERSION,
        "status": STATUS_AWAITING,
        "sourceDocument": {
            "sourceType": source_type,
            "source": normalized_content[:5000],  # Truncate to 5000 chars
            "sourceFormat": source_format,
        },
        "knowledgeIndex": {
            "references": extracted_refs.get("references", []),
        },
    }

    manifest["manifestId"] = uuid4().hex
    manifest["processedAt"] = datetime.now(UTC).isoformat()

    return manifest


def count_references_by_type(refs: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Count references by their type.

    Args:
        refs: List of reference dictionaries

    Returns:
        Tuple of (url_count, citation_count, total_count)
    """
    url_count = sum(1 for r in refs if r.get("referenceType") == "web_link")
    citation_count = sum(
        1 for r in refs if r.get("referenceType") == "in_text_citation"
    )
    total_count = len(refs)

    return url_count, citation_count, total_count
