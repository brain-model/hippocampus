from __future__ import annotations

import pytest

from core.application.validation import validate_manifest


def test_validate_manifest_ok(schema_path: str):
    manifest = {
        "manifestVersion": "1.0.0",
        "manifestId": "x",
        "processedAt": "2020-01-01T00:00:00Z",
        "status": "Awaiting Consolidation",
        "sourceDocument": {"sourceType": "text", "source": "x", "sourceFormat": "text"},
        "knowledgeIndex": {"references": []},
    }
    validate_manifest(manifest, schema_path)


def test_validate_manifest_fail(schema_path: str):
    bad = {"manifestVersion": "1.0.0"}
    with pytest.raises(ValueError) as ei:
        validate_manifest(bad, schema_path)
    assert "Manifest validation failed" in str(ei.value)
