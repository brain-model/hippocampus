"""Tests for the assemble module."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from core.application.pipeline.assemble import (
    assemble_manifest,
    count_references_by_type,
)


class TestAssembleManifest:
    """Tests for assemble_manifest function."""

    def test_assembles_basic_manifest(self):
        """Test assembling a basic manifest."""
        normalized_content = "Test content"
        extracted_refs = {
            "references": [
                {
                    "id": 1,
                    "referenceType": "web_link",
                    "rawString": "https://example.com",
                    "sourceFormat": "web_content",
                    "sourcePath": "https://example.com",
                    "details": {},
                }
            ]
        }

        manifest = assemble_manifest(
            normalized_content, extracted_refs, source_type="text", source_format="text"
        )

        # Check basic structure
        assert manifest["manifestVersion"] == "1.0.0"
        assert manifest["status"] == "Awaiting Consolidation"
        assert "manifestId" in manifest
        assert "processedAt" in manifest

        # Check manifestId is valid UUID
        UUID(manifest["manifestId"])  # Should not raise exception

        # Check processedAt is valid ISO datetime
        datetime.fromisoformat(manifest["processedAt"])  # Should not raise exception

        # Check sourceDocument
        assert manifest["sourceDocument"]["sourceType"] == "text"
        assert manifest["sourceDocument"]["sourceFormat"] == "text"
        assert manifest["sourceDocument"]["source"] == normalized_content

        # Check knowledgeIndex
        assert manifest["knowledgeIndex"]["references"] == extracted_refs["references"]

    def test_assembles_manifest_with_empty_references(self):
        """Test assembling manifest with empty references."""
        normalized_content = "Content without references"
        extracted_refs = {"references": []}

        manifest = assemble_manifest(normalized_content, extracted_refs)

        assert manifest["knowledgeIndex"]["references"] == []

    def test_assembles_manifest_with_multiple_references(self):
        """Test assembling manifest with multiple references."""
        normalized_content = "Content with multiple references"
        extracted_refs = {
            "references": [
                {
                    "id": 1,
                    "referenceType": "web_link",
                    "rawString": "https://example.com",
                    "sourceFormat": "web_content",
                    "sourcePath": "https://example.com",
                    "details": {},
                },
                {
                    "id": 2,
                    "referenceType": "in_text_citation",
                    "rawString": "Smith (2020)",
                    "sourceFormat": "text",
                    "sourcePath": "",
                    "details": {},
                },
            ]
        }

        manifest = assemble_manifest(normalized_content, extracted_refs)

        assert len(manifest["knowledgeIndex"]["references"]) == 2
        assert manifest["knowledgeIndex"]["references"][0]["id"] == 1
        assert manifest["knowledgeIndex"]["references"][1]["id"] == 2

    def test_assembles_file_manifest(self):
        """Test assembling manifest from file source."""
        normalized_content = "File content"
        extracted_refs = {"references": []}

        manifest = assemble_manifest(
            normalized_content, extracted_refs, source_type="file", source_format="md"
        )

        assert manifest["sourceDocument"]["sourceType"] == "file"
        assert manifest["sourceDocument"]["sourceFormat"] == "md"

    def test_each_manifest_has_unique_id(self):
        """Test that each manifest gets a unique ID."""
        normalized_content = "Test content"
        extracted_refs = {"references": []}

        manifest1 = assemble_manifest(normalized_content, extracted_refs)
        manifest2 = assemble_manifest(normalized_content, extracted_refs)

        assert manifest1["manifestId"] != manifest2["manifestId"]

    def test_manifest_processed_at_is_recent(self):
        """Test that processedAt timestamp is recent."""
        normalized_content = "Test content"
        extracted_refs = {"references": []}

        manifest = assemble_manifest(normalized_content, extracted_refs)
        processed_at = datetime.fromisoformat(manifest["processedAt"])

        # Should be a valid datetime with timezone
        assert processed_at.tzinfo is not None

        # Should be within the last minute (very generous)
        from datetime import timedelta

        now_utc = datetime.now(UTC)
        one_minute_ago = now_utc - timedelta(minutes=1)

        assert processed_at >= one_minute_ago
        assert processed_at <= now_utc


class TestCountReferencesByType:
    """Tests for count_references_by_type function."""

    def test_counts_empty_references(self):
        """Test counting empty references list."""
        refs = []
        url_count, citation_count, total_refs = count_references_by_type(refs)

        assert url_count == 0
        assert citation_count == 0
        assert total_refs == 0

    def test_counts_web_links(self):
        """Test counting web link references."""
        refs = [
            {
                "id": 1,
                "referenceType": "web_link",
                "rawString": "https://example.com",
                "sourceFormat": "web_content",
                "sourcePath": "https://example.com",
                "details": {},
            },
            {
                "id": 2,
                "referenceType": "web_link",
                "rawString": "https://another.com",
                "sourceFormat": "web_content",
                "sourcePath": "https://another.com",
                "details": {},
            },
        ]

        url_count, citation_count, total_refs = count_references_by_type(refs)

        assert url_count == 2
        assert citation_count == 0
        assert total_refs == 2

    def test_counts_citations(self):
        """Test counting citation references."""
        refs = [
            {
                "id": 1,
                "referenceType": "in_text_citation",
                "rawString": "Smith (2020)",
                "sourceFormat": "text",
                "sourcePath": "",
                "details": {},
            },
            {
                "id": 2,
                "referenceType": "in_text_citation",
                "rawString": "Jones, A. (2021). Title. Journal.",
                "sourceFormat": "text",
                "sourcePath": "",
                "details": {},
            },
        ]

        url_count, citation_count, total_refs = count_references_by_type(refs)

        assert url_count == 0
        assert citation_count == 2
        assert total_refs == 2

    def test_counts_mixed_references(self):
        """Test counting mixed reference types."""
        refs = [
            {
                "id": 1,
                "referenceType": "web_link",
                "rawString": "https://example.com",
                "sourceFormat": "web_content",
                "sourcePath": "https://example.com",
                "details": {},
            },
            {
                "id": 2,
                "referenceType": "in_text_citation",
                "rawString": "Smith (2020)",
                "sourceFormat": "text",
                "sourcePath": "",
                "details": {},
            },
            {
                "id": 3,
                "referenceType": "in_text_citation",
                "rawString": "Jones, A. (2021). Title. Journal.",
                "sourceFormat": "text",
                "sourcePath": "",
                "details": {},
            },
        ]

        url_count, citation_count, total_refs = count_references_by_type(refs)

        assert url_count == 1
        assert citation_count == 2
        assert total_refs == 3

    def test_counts_unknown_types_as_other(self):
        """Test that unknown reference types are not counted as citations."""
        refs = [
            {
                "id": 1,
                "referenceType": "unknown_type",
                "rawString": "Unknown reference",
                "sourceFormat": "text",
                "sourcePath": "",
                "details": {},
            }
        ]

        url_count, citation_count, total_refs = count_references_by_type(refs)

        assert url_count == 0
        assert citation_count == 0  # Unknown types are not counted as citations
        assert total_refs == 1


class TestAssembleModule:
    """Integration tests for the assemble module."""

    def test_assemble_and_count_integration(self):
        """Test integration between assemble_manifest and count_references_by_type."""
        normalized_content = "Content with mixed references"
        extracted_refs = {
            "references": [
                {
                    "id": 1,
                    "referenceType": "web_link",
                    "rawString": "https://example.com",
                    "sourceFormat": "web_content",
                    "sourcePath": "https://example.com",
                    "details": {},
                },
                {
                    "id": 2,
                    "referenceType": "in_text_citation",
                    "rawString": "Smith (2020)",
                    "sourceFormat": "text",
                    "sourcePath": "",
                    "details": {},
                },
            ]
        }

        # Assemble manifest
        manifest = assemble_manifest(normalized_content, extracted_refs)

        # Count references from assembled manifest
        refs = manifest["knowledgeIndex"]["references"]
        url_count, citation_count, total_refs = count_references_by_type(refs)

        assert url_count == 1
        assert citation_count == 1
        assert total_refs == 2

        # References should be preserved exactly
        assert manifest["knowledgeIndex"]["references"] == extracted_refs["references"]
