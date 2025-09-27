"""Simplified tests for the validate module."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.application.pipeline.validate import validate_manifest


def _get_test_schema_path() -> str:
    """Get the path to the manifest schema file for tests."""
    base = Path(__file__).parent.parent.parent.parent
    return str(base / "core" / "resources" / "schemas" / "manifest.schema.json")


class TestValidateManifestSimple:
    """Simplified tests for validate_manifest function."""

    def test_validates_correct_manifest(self):
        """Test validating a correct manifest."""
        manifest = {
            "manifestVersion": "1.0.0",
            "status": "Awaiting Consolidation",
            "manifestId": "test-id",
            "processedAt": "2023-01-01T00:00:00Z",
            "sourceDocument": {
                "source": "test content",
                "sourceType": "text",
                "sourceFormat": "text",
            },
            "knowledgeIndex": {"references": []},
        }

        # Should not raise exception for valid manifest
        validate_manifest(manifest, _get_test_schema_path())

    def test_raises_error_for_invalid_version(self):
        """Test that invalid manifestVersion raises error."""
        manifest = {
            "manifestVersion": "0.9.0",  # Invalid: < 1.0.0
            "status": "Awaiting Consolidation",
            "manifestId": "test-id",
            "processedAt": "2023-01-01T00:00:00Z",
            "sourceDocument": {
                "source": "test content",
                "sourceType": "text",
                "sourceFormat": "text",
            },
            "knowledgeIndex": {"references": []},
        }

        with pytest.raises(ValueError, match="unsupported"):
            validate_manifest(manifest, _get_test_schema_path())

    def test_raises_error_for_incompatible_version(self):
        """Test that incompatible manifestVersion raises error."""
        manifest = {
            "manifestVersion": "2.0.0",  # Invalid: >= 2.0.0
            "status": "Awaiting Consolidation",
            "manifestId": "test-id",
            "processedAt": "2023-01-01T00:00:00Z",
            "sourceDocument": {
                "source": "test content",
                "sourceType": "text",
                "sourceFormat": "text",
            },
            "knowledgeIndex": {"references": []},
        }

        with pytest.raises(ValueError, match="incompatible major"):
            validate_manifest(manifest, _get_test_schema_path())

    def test_raises_error_for_missing_fields(self):
        """Test that missing required fields raise error."""
        manifest = {
            "manifestVersion": "1.0.0",
            # Missing required fields like status, manifestId, etc.
        }

        with pytest.raises(ValueError, match="Manifest validation failed"):
            validate_manifest(manifest, _get_test_schema_path())
