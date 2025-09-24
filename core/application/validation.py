"""Validation utilities for manifests using JSON Schema (Draft-07).

This module exposes helpers to validate a manifest dictionary against the
project's canonical JSON Schema, raising detailed errors on violations.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

# Constants for SemVer validation
SEMVER_PARTS_COUNT = 3
MIN_MAJOR_VERSION = 1
MAX_MAJOR_VERSION = 2


def _parse_semver(ver: str) -> tuple[int, int, int]:
    parts = ver.split(".")
    if len(parts) != SEMVER_PARTS_COUNT or not all(p.isdigit() for p in parts):
        raise ValueError(f"Invalid SemVer: {ver}")
    return tuple(int(p) for p in parts)  # type: ignore[return-value]


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
    errors = sorted(
        validator.iter_errors(manifest),
        key=lambda e: (tuple(e.path), getattr(e, "validator", ""), e.message),
    )
    if errors:

        def _loc(e: object) -> str:  # type: ignore[no-redef]
            try:
                # jsonschema errors expose .path as a deque-like of path components
                parts = list(getattr(e, "path", []))
                return "/".join(map(str, parts)) if parts else "<root>"
            except Exception:
                return "<root>"

        msgs = [f"{_loc(e)}: {getattr(e, 'message', str(e))}" for e in errors]
        raise ValueError("Manifest validation failed: " + "; ".join(msgs))

    # Compatibility check for manifestVersion: accept >=1.0.0 and <2.0.0
    mv = manifest.get("manifestVersion")
    if not isinstance(mv, str):
        raise ValueError(
            "Manifest validation failed: manifestVersion: must be a string SemVer x.y.z"
        )
    try:
        major, _minor, _patch = _parse_semver(mv)
    except ValueError as e:
        raise ValueError(f"Manifest validation failed: manifestVersion: {e}") from e
    if major < MIN_MAJOR_VERSION:
        raise ValueError(
            "Manifest validation failed: manifestVersion: "
            "unsupported (requires >=1.0.0)"
        )
    if major >= MAX_MAJOR_VERSION:
        raise ValueError(
            "Manifest validation failed: manifestVersion: "
            "incompatible major (requires <2.0.0)"
        )
