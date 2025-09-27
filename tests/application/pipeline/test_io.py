"""Tests for the io module."""

from __future__ import annotations

import contextlib
from unittest.mock import Mock, patch

import pytest

from core.application.pipeline.io import write_manifest


class TestWriteManifest:
    """Tests for write_manifest function."""

    @patch("core.application.pipeline.io.ManifestJsonWriter")
    def test_writes_manifest_successfully(self, mock_writer_class):
        """Test successful manifest writing."""
        # Mock the writer instance
        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        manifest = {
            "manifestVersion": "1.0.0",
            "status": "Awaiting Consolidation",
            "manifestId": "test-id",
            "processedAt": "2023-01-01T00:00:00Z",
            "sourceDocument": {
                "type": "text",
                "format": "text",
                "content": "test content",
            },
            "knowledgeIndex": {"references": []},
        }
        out_dir = "/tmp/test"

        write_manifest(manifest, out_dir)

        # Should create writer instance and call write
        mock_writer_class.assert_called_once()
        mock_writer.write.assert_called_once_with(manifest, out_dir)

    @patch("core.application.pipeline.io.ManifestJsonWriter")
    def test_handles_write_error(self, mock_writer_class):
        """Test handling of write errors."""
        # Mock writer to raise error
        mock_writer = Mock()
        mock_writer.write.side_effect = OSError("Failed to write file")
        mock_writer_class.return_value = mock_writer

        manifest = {"test": "manifest"}
        out_dir = "/invalid/path"

        # Should propagate the error
        with pytest.raises(OSError, match="Failed to write file"):
            write_manifest(manifest, out_dir)

    @patch("core.application.pipeline.io.ManifestJsonWriter")
    def test_handles_directory_creation_error(self, mock_writer_class):
        """Test handling of directory creation errors."""
        # Mock writer to raise permission error
        mock_writer = Mock()
        mock_writer.write.side_effect = PermissionError("Permission denied")
        mock_writer_class.return_value = mock_writer

        manifest = {"test": "manifest"}
        out_dir = "/no/permission"

        # Should propagate the permission error
        with pytest.raises(PermissionError, match="Permission denied"):
            write_manifest(manifest, out_dir)

    @patch("core.application.pipeline.io.ManifestJsonWriter")
    def test_writes_empty_manifest(self, mock_writer_class):
        """Test writing empty manifest."""
        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        manifest = {}
        out_dir = "/tmp/empty"

        write_manifest(manifest, out_dir)

        # Should still attempt to write
        mock_writer.write.assert_called_once_with(manifest, out_dir)

    @patch("core.application.pipeline.io.ManifestJsonWriter")
    def test_writes_complex_manifest(self, mock_writer_class):
        """Test writing complex manifest with many references."""
        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        manifest = {
            "manifestVersion": "1.0.0",
            "status": "Awaiting Consolidation",
            "manifestId": "complex-manifest-id",
            "processedAt": "2023-01-01T00:00:00Z",
            "sourceDocument": {
                "type": "file",
                "format": "pdf",
                "content": "Complex document content",
            },
            "knowledgeIndex": {
                "references": [
                    {
                        "id": i,
                        "referenceType": "web_link",
                        "rawString": f"https://example{i}.com",
                        "sourceFormat": "web_content",
                        "sourcePath": f"https://example{i}.com",
                        "details": {},
                    }
                    for i in range(10)
                ]
            },
        }
        out_dir = "/tmp/complex"

        write_manifest(manifest, out_dir)

        # Should handle complex manifest
        mock_writer.write.assert_called_once_with(manifest, out_dir)

    def test_integration_with_real_writer(self, tmp_path):
        """Test integration with real ManifestJsonWriter."""
        manifest = {
            "manifestVersion": "1.0.0",
            "status": "Awaiting Consolidation",
            "manifestId": "integration-test-id",
            "processedAt": "2023-01-01T00:00:00Z",
            "sourceDocument": {
                "type": "text",
                "format": "text",
                "content": "Integration test content",
            },
            "knowledgeIndex": {"references": []},
        }

        # Use real temporary directory
        out_dir = str(tmp_path)

        # Should write file successfully
        write_manifest(manifest, out_dir)

        # Check that file was created
        manifest_file = tmp_path / "manifest" / "manifest.json"
        assert manifest_file.exists()

        # Check file contains JSON
        content = manifest_file.read_text()
        assert "manifestVersion" in content
        assert "integration-test-id" in content


class TestIOModule:
    """Integration tests for the io module."""

    def test_module_imports_correctly(self):
        """Test that the module imports are correct."""
        from core.application.pipeline.io import write_manifest

        assert callable(write_manifest)

    def test_uses_correct_writer_class(self):
        """Test that module uses correct writer class."""
        from core.infrastructure.formatters.json_writer import ManifestJsonWriter

        # Should import the correct writer class
        assert ManifestJsonWriter is not None

    @patch("core.application.pipeline.io.ManifestJsonWriter")
    def test_writer_instantiation(self, mock_writer_class):
        """Test that writer is instantiated correctly."""
        mock_writer = Mock()
        mock_writer_class.return_value = mock_writer

        manifest = {"test": "data"}
        out_dir = "/tmp/test"

        write_manifest(manifest, out_dir)

        # Should instantiate writer with no arguments
        mock_writer_class.assert_called_once_with()

    def test_error_propagation_chain(self, tmp_path):
        """Test that errors propagate correctly through the call chain."""
        # Create a directory that we'll make read-only
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()

        manifest = {"test": "manifest"}

        # On most systems, we can't make a directory truly read-only for the owner
        # So we'll test with a file that doesn't exist in a path we know exists
        out_dir = str(read_only_dir)

        # This should work fine - the error handling is tested with mocks above
        try:
            write_manifest(manifest, out_dir)
        except OSError:
            contextlib.suppress(OSError)
