from __future__ import annotations

import pytest

from core.application.validation import validate_manifest

BASE = {
    "manifestId": "id",
    "processedAt": "2024-01-01T00:00:00Z",
    "status": "Awaiting Consolidation",
    "sourceDocument": {"sourceType": "text", "source": "x", "sourceFormat": "text"},
    "knowledgeIndex": {"references": []},
}


def _wrap(ver: object):
    m = dict(BASE)
    m["manifestVersion"] = ver  # type: ignore[index]
    return m


def test_manifest_version_ok(schema_path: str):
    validate_manifest(_wrap("1.0.0"), schema_path)
    validate_manifest(_wrap("1.2.3"), schema_path)


def test_manifest_version_invalid_format(schema_path: str):
    # Formato inválido é pego pelo JSON Schema (pattern)
    with pytest.raises(ValueError, match="does not match"):
        validate_manifest(_wrap("1.0"), schema_path)


def test_manifest_version_incompatible_major(schema_path: str):
    with pytest.raises(ValueError, match="incompatible major"):
        validate_manifest(_wrap("2.0.0"), schema_path)


def test_manifest_version_unsupported_major(schema_path: str):
    with pytest.raises(ValueError, match="unsupported"):
        validate_manifest(_wrap("0.9.9"), schema_path)


def test_manifest_version_missing(schema_path: str):
    # Remove a chave e espera erro do schema antes do semver
    bad = dict(BASE)
    with pytest.raises(ValueError, match="manifestVersion"):
        validate_manifest(bad, schema_path)
