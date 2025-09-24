"""Domain types for the Hippocampus manifest model.

Defines TypedDict structures and constants that describe the canonical
manifest format produced and consumed by the application pipeline.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

MANIFEST_VERSION: str = "1.0.0"
STATUS_AWAITING: Literal["Awaiting Consolidation"] = "Awaiting Consolidation"


class SourceDocument(TypedDict):
    """Primary source of the processed knowledge.

    Represents the input document used during extraction/normalization.
    """

    sourceType: Literal["text", "file"]
    source: str
    sourceFormat: str


class Reference(TypedDict, total=False):
    """Bibliographic reference or URL extracted from the content."""

    id: int
    rawString: str
    referenceType: str
    sourceFormat: str
    sourcePath: str
    details: dict[str, Any]


class KnowledgeIndex(TypedDict):
    """Index consolidating extracted knowledge structures."""

    references: list[Reference]


class Manifest(TypedDict):
    """Hippocampus standardized manifest.

    Canonical structure validated by JSON Schema that aggregates source
    metadata and extracted indices for later use.
    """

    manifestVersion: str
    manifestId: str
    processedAt: str
    status: Literal["Awaiting Consolidation"]
    sourceDocument: SourceDocument
    knowledgeIndex: KnowledgeIndex
