"""Application layer."""

# Re-export the main pipeline functions to maintain backward compatibility
from .pipeline import (
    build_manifest_from_file,
    build_manifest_from_text,
    validate_manifest,
)

__all__ = [
    "build_manifest_from_file",
    "build_manifest_from_text",
    "validate_manifest",
]
