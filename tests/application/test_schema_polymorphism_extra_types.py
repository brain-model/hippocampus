from __future__ import annotations

import pytest

from core.application.validation import validate_manifest

BASE = {
    "manifestVersion": "1.0.0",
    "manifestId": "id",
    "processedAt": "2024-01-01T00:00:00Z",
    "status": "Awaiting Consolidation",
    "sourceDocument": {"sourceType": "text", "source": "x", "sourceFormat": "text"},
}


def wrap(ref):
    return {**BASE, "knowledgeIndex": {"references": [ref]}}


def test_article_ok(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "Some Article",
        "referenceType": "article",
        "sourceFormat": "text",
        "sourcePath": "",
        "details": {
            "title": "A",
            "authors": ["Doe"],
            "journal": "J",
            "year": 2020,
            "doi": "10.1000/xyz"
        },
    }
    validate_manifest(wrap(ref), schema_path)


def test_article_reject_unknown(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "Some Article",
        "referenceType": "article",
        "sourceFormat": "text",
        "sourcePath": "",
        "details": {"unknown": True},
    }
    with pytest.raises(ValueError):
        validate_manifest(wrap(ref), schema_path)


def test_book_ok(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "Some Book",
        "referenceType": "book",
        "sourceFormat": "text",
        "sourcePath": "",
        "details": {"title": "B", "authors": ["Doe"], "publisher": "P", "year": 2020},
    }
    validate_manifest(wrap(ref), schema_path)


def test_book_reject_unknown(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "Some Book",
        "referenceType": "book",
        "sourceFormat": "text",
        "sourcePath": "",
        "details": {"publisher": "P", "extra": 1},
    }
    with pytest.raises(ValueError):
        validate_manifest(wrap(ref), schema_path)


def test_website_ok(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "https://example.com",
        "referenceType": "website",
        "sourceFormat": "web_content",
        "sourcePath": "https://example.com",
        "details": {"title": "T", "site_name": "Example"},
    }
    validate_manifest(wrap(ref), schema_path)


def test_website_reject_unknown(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "https://example.com",
        "referenceType": "website",
        "sourceFormat": "web_content",
        "sourcePath": "https://example.com",
        "details": {"title": "T", "bogus": 1},
    }
    with pytest.raises(ValueError):
        validate_manifest(wrap(ref), schema_path)


def test_thesis_ok(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "Some Thesis",
        "referenceType": "thesis",
        "sourceFormat": "text",
        "sourcePath": "",
        "details": {"title": "T", "authors": ["Doe"], "university": "U", "year": 2020},
    }
    validate_manifest(wrap(ref), schema_path)


def test_conference_ok(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "Some Conf",
        "referenceType": "conference",
        "sourceFormat": "text",
        "sourcePath": "",
        "details": {"title": "T", "conference": "C", "year": 2020},
    }
    validate_manifest(wrap(ref), schema_path)


def test_unknown_ok(schema_path: str):
    ref = {
        "id": 1,
        "rawString": "X",
        "referenceType": "unknown",
        "sourceFormat": "text",
        "sourcePath": "",
        "details": {"title": "T"},
    }
    validate_manifest(wrap(ref), schema_path)
