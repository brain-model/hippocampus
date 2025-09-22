from __future__ import annotations

import pytest

from core.application.validation import validate_manifest


BASE_MANIFEST = {
    "manifestVersion": "1.0.0",
    "manifestId": "abc",
    "processedAt": "2024-01-01T00:00:00Z",
    "status": "Awaiting Consolidation",
    "sourceDocument": {"sourceType": "text", "source": "x", "sourceFormat": "text"},
}


def _wrap(refs):
    return {
        **BASE_MANIFEST,
        "knowledgeIndex": {"references": refs},
    }


def test_web_link_details_allow_empty(schema_path: str):
    manifest = _wrap([
        {
            "id": 1,
            "rawString": "https://example.com",
            "referenceType": "web_link",
            "sourceFormat": "web_content",
            "sourcePath": "https://example.com",
            "details": {},
        }
    ])
    validate_manifest(manifest, schema_path)


def test_web_link_details_reject_unknown_field(schema_path: str):
    manifest = _wrap([
        {
            "id": 1,
            "rawString": "https://example.com",
            "referenceType": "web_link",
            "sourceFormat": "web_content",
            "sourcePath": "https://example.com",
            "details": {"unexpected": 123},
        }
    ])
    with pytest.raises(ValueError):
        validate_manifest(manifest, schema_path)


def test_in_text_citation_minimal_ok(schema_path: str):
    manifest = _wrap([
        {
            "id": 1,
            "rawString": "Doe (2020)",
            "referenceType": "in_text_citation",
            "sourceFormat": "text",
            "sourcePath": "",
            "details": {"author": "Doe", "year": 2020},
        }
    ])
    validate_manifest(manifest, schema_path)


def test_in_text_citation_reject_unknown_field(schema_path: str):
    manifest = _wrap([
        {
            "id": 1,
            "rawString": "Doe (2020)",
            "referenceType": "in_text_citation",
            "sourceFormat": "text",
            "sourcePath": "",
            "details": {"author": "Doe", "year": 2020, "extra": True},
        }
    ])
    with pytest.raises(ValueError):
        validate_manifest(manifest, schema_path)
