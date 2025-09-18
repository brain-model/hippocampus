"""Validation utilities for manifests using JSON Schema (Draft-07).

This module exposes helpers to validate a manifest dictionary against the
project's canonical JSON Schema, raising detailed errors on violations.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator


def validate_manifest(manifest: dict, schema_path: str) -> None:
    """Validate a manifest against a Draft-07 JSON Schema.

    Reads the schema from the given path, instantiates a `Draft7Validator`,
    and raises `ValueError` with aggregated details if any inconsistencies
    are found.

    Args:
        manifest: Manifest dictionary to validate.
        schema_path: Absolute path to the JSON Schema file.

    Raises:
        ValueError: When validation detects non-conformities.
    """
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
    if errors:
        msgs = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in errors]
        raise ValueError("Manifest validation failed: " + "; ".join(msgs))
