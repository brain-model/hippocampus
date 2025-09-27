"""Pipeline application module.

This module provides a clean separation of concerns for the manifest pipeline:
- load: Document loading and normalization
- extract: Extraction adapters (heuristic/LLM/graph)
- assemble: Manifest assembly with metadata
- validate: Schema validation
- metrics: Metrics aggregation
- report: Template rendering
- io: File I/O operations
- core: Main pipeline orchestration

Public API exports for backward compatibility.
"""

from __future__ import annotations

# Import sub-modules for tests that still reference them
from core.application.pipeline import io, validate
from core.application.pipeline.assemble import (
    assemble_manifest,
    count_references_by_type,
)

# Re-export main pipeline functions
from core.application.pipeline.core import (
    build_manifest_from_file,
    build_manifest_from_text,
)

# Re-export other commonly used functions
from core.application.pipeline.extract import create_extractor, get_engine_mode
from core.application.pipeline.io import write_manifest
from core.application.pipeline.load import load_file_content, load_text_content
from core.application.pipeline.metrics import log_pipeline_metrics
from core.application.pipeline.validate import validate_manifest
from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent

# Import classes for test compatibility
from core.infrastructure.loaders.text import TextLoader

__all__ = [
    "build_manifest_from_text",
    "build_manifest_from_file",
    "create_extractor",
    "get_engine_mode",
    "load_text_content",
    "load_file_content",
    "assemble_manifest",
    "count_references_by_type",
    "validate_manifest",
    "write_manifest",
    "log_pipeline_metrics",
    "validate",
    "io",
    "TextLoader",
    "HeuristicExtractionAgent",
]
