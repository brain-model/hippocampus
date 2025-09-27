"""Tests for the core module."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from core.application.pipeline.core import (
    build_manifest_from_file,
    build_manifest_from_text,
    line,
    summary_panel,
)


class TestWrapperFunctions:
    """Tests for wrapper functions used for test compatibility."""

    @patch("core.ui.console.line")
    def test_line_wrapper(self, mock_console_line):
        """Test line wrapper function."""
        line("test message")
        mock_console_line.assert_called_once_with("test message")

    @patch("core.ui.console.summary_panel")
    def test_summary_panel_wrapper(self, mock_summary_panel):
        """Test summary_panel wrapper function."""
        summary_panel("Test Title", "Test Content")
        mock_summary_panel.assert_called_once_with("Test Title", "Test Content")


class TestBuildManifestFromText:
    """Tests for build_manifest_from_text function."""

    @patch("core.application.pipeline.core.render_report_and_end")
    @patch("core.application.pipeline.core.write_manifest")
    @patch("core.application.pipeline.core.validate_manifest")
    @patch("core.application.pipeline.core.assemble_manifest")
    @patch("core.application.pipeline.core.create_extractor")
    @patch("core.application.pipeline.core.load_text_content")
    def test_builds_manifest_from_text_basic(
        self,
        mock_load,
        mock_create,
        mock_assemble,
        mock_validate,
        mock_write,
        mock_render,
    ):
        """Test basic manifest building from text."""
        # Mock dependencies
        mock_load.return_value = "normalized content"

        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"references": []}
        mock_create.return_value = mock_extractor

        mock_manifest = {
            "manifestId": "test-id",
            "status": "Awaiting Consolidation",
            "processedAt": "2024-01-01T00:00:00Z",
        }
        mock_assemble.return_value = mock_manifest

        # Call function
        result = build_manifest_from_text("test text", "/tmp/out")

        # Verify flow
        mock_load.assert_called_once_with("test text")
        mock_create.assert_called_once_with("heuristic", None, None)
        mock_extractor.extract.assert_called_once_with("normalized content")
        mock_assemble.assert_called_once_with(
            "normalized content", {"references": []}, "text", "text"
        )
        # validate_manifest now requires schema_path as second argument
        mock_validate.assert_called_once()
        assert (
            mock_validate.call_args[0][0] == mock_manifest
        )  # First argument is manifest
        # Second argument is schema path
        assert mock_validate.call_args[0][1].endswith("manifest.schema.json")
        mock_write.assert_called_once_with(mock_manifest, "/tmp/out")
        mock_render.assert_called_once()

        assert result == mock_manifest

    @patch("core.application.pipeline.core.render_report_and_end")
    @patch("core.application.pipeline.core.write_manifest")
    @patch("core.application.pipeline.core.validate_manifest")
    @patch("core.application.pipeline.core.assemble_manifest")
    @patch("core.application.pipeline.core.create_extractor")
    @patch("core.application.pipeline.core.load_text_content")
    @patch("core.application.pipeline.core.collect_section")
    def test_builds_manifest_non_verbose_mode(
        self,
        mock_collect,
        mock_load,
        mock_create,
        mock_assemble,
        mock_validate,
        mock_write,
        mock_render,
    ):
        """Test building manifest in non-verbose mode."""
        # Mock dependencies
        mock_load.return_value = "content"
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"references": []}
        mock_create.return_value = mock_extractor
        mock_manifest = {"manifestId": "test-id"}
        mock_assemble.return_value = mock_manifest

        # Mock context manager
        mock_collect_context = Mock()
        mock_collect.return_value.__enter__ = Mock(return_value=mock_collect_context)
        mock_collect.return_value.__exit__ = Mock(return_value=None)

        result = build_manifest_from_text("test", "/tmp", verbose=False)

        # Should use collect_section for non-verbose
        mock_collect.assert_called_once_with("Collect")
        assert result == mock_manifest

    @patch("core.application.pipeline.core.render_report_and_end")
    @patch("core.application.pipeline.core.write_manifest")
    @patch("core.application.pipeline.core.validate_manifest")
    @patch("core.application.pipeline.core.assemble_manifest")
    @patch("core.application.pipeline.core.create_extractor")
    @patch("core.application.pipeline.core.load_text_content")
    @patch("core.application.pipeline.core.line")
    def test_builds_manifest_verbose_mode(
        self,
        mock_line,
        mock_load,
        mock_create,
        mock_assemble,
        mock_validate,
        mock_write,
        mock_render,
    ):
        """Test building manifest in verbose mode."""
        # Mock dependencies
        mock_load.return_value = "content"
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"references": []}
        mock_create.return_value = mock_extractor
        mock_manifest = {"manifestId": "test-id"}
        mock_assemble.return_value = mock_manifest

        result = build_manifest_from_text("test", "/tmp", verbose=True)

        # Should call line function for verbose logging
        mock_line.assert_called()
        assert result == mock_manifest

    @patch("core.application.pipeline.core.create_extractor")
    def test_uses_specified_engine(self, mock_create):
        """Test that specified engine is used."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"references": []}
        mock_create.return_value = mock_extractor

        with (
            patch("core.application.pipeline.core.write_manifest"),
            patch("core.application.pipeline.core.validate_manifest"),
            patch("core.application.pipeline.core.assemble_manifest") as mock_assemble,
            patch("core.application.pipeline.core.load_text_content"),
            patch("core.application.pipeline.core.render_report_and_end"),
        ):
            mock_assemble.return_value = {
                "manifestId": "test",
                "processedAt": "2024-01-01T00:00:00Z",
            }

            build_manifest_from_text("test", "/tmp", engine="llm")

            # Should create extractor with specified engine
            mock_create.assert_called_once_with("llm", None, None)

    @patch("core.application.pipeline.core.create_extractor")
    def test_passes_engine_overrides(self, mock_create):
        """Test that engine overrides are passed correctly."""
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"references": []}
        mock_create.return_value = mock_extractor

        with (
            patch("core.application.pipeline.core.write_manifest"),
            patch("core.application.pipeline.core.validate_manifest"),
            patch("core.application.pipeline.core.assemble_manifest") as mock_assemble,
            patch("core.application.pipeline.core.load_text_content"),
            patch("core.application.pipeline.core.render_report_and_end"),
        ):
            mock_assemble.return_value = {
                "manifestId": "test",
                "processedAt": "2024-01-01T00:00:00Z",
            }
            overrides = {"provider": "openai", "model": "gpt-4"}

            build_manifest_from_text("test", "/tmp", engine_overrides=overrides)

            # Should pass overrides to create_extractor
            mock_create.assert_called_once_with("heuristic", overrides, None)


class TestBuildManifestFromFile:
    """Tests for build_manifest_from_file function."""

    @patch("core.application.pipeline.core.render_report_and_end")
    @patch("core.application.pipeline.core.write_manifest")
    @patch("core.application.pipeline.core.validate_manifest")
    @patch("core.application.pipeline.core.assemble_manifest")
    @patch("core.application.pipeline.core.create_extractor")
    @patch("core.application.pipeline.core.load_file_content")
    def test_builds_manifest_from_file_basic(
        self,
        mock_load,
        mock_create,
        mock_assemble,
        mock_validate,
        mock_write,
        mock_render,
    ):
        """Test basic manifest building from file."""
        # Mock dependencies
        mock_load.return_value = "file content"

        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"references": []}
        mock_create.return_value = mock_extractor

        mock_manifest = {
            "manifestId": "file-test-id",
            "status": "Awaiting Consolidation",
        }
        mock_assemble.return_value = mock_manifest

        # Call function
        result = build_manifest_from_file("/path/to/test.md", "/tmp/out")

        # Verify flow
        mock_load.assert_called_once_with("/path/to/test.md")
        mock_create.assert_called_once_with("heuristic", None, None)
        mock_extractor.extract.assert_called_once_with("file content")
        mock_assemble.assert_called_once_with(
            "file content", {"references": []}, "file", "md"
        )
        # validate_manifest now requires schema_path as second argument
        mock_validate.assert_called_once()
        assert (
            mock_validate.call_args[0][0] == mock_manifest
        )  # First argument is manifest
        # Second argument is schema path
        assert mock_validate.call_args[0][1].endswith("manifest.schema.json")
        mock_write.assert_called_once_with(mock_manifest, "/tmp/out")

        assert result == mock_manifest

    @patch("core.application.pipeline.core.render_report_and_end")
    @patch("core.application.pipeline.core.write_manifest")
    @patch("core.application.pipeline.core.validate_manifest")
    @patch("core.application.pipeline.core.assemble_manifest")
    @patch("core.application.pipeline.core.create_extractor")
    @patch("core.application.pipeline.core.load_file_content")
    def test_detects_file_format_correctly(
        self,
        mock_load,
        mock_create,
        mock_assemble,
        mock_validate,
        mock_write,
        mock_render,
    ):
        """Test that file format is detected correctly from extension."""
        mock_load.return_value = "content"
        mock_extractor = Mock()
        mock_extractor.extract.return_value = {"references": []}
        mock_create.return_value = mock_extractor
        mock_manifest = {"manifestId": "test"}
        mock_assemble.return_value = mock_manifest

        test_cases = [
            ("/path/file.txt", "txt"),
            ("/path/file.md", "md"),
            ("/path/file.pdf", "pdf"),
            ("/path/file", "unknown"),
        ]

        for file_path, expected_format in test_cases:
            mock_assemble.reset_mock()
            build_manifest_from_file(file_path, "/tmp")

            # Check that assemble was called with correct format
            args = mock_assemble.call_args[0]
            assert args[2] == "file"  # source_type
            assert args[3] == expected_format  # source_format

    @patch("core.application.pipeline.core.load_file_content")
    def test_handles_file_load_error(self, mock_load):
        """Test handling of file load errors."""
        mock_load.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError, match="File not found"):
            build_manifest_from_file("/nonexistent/file.txt", "/tmp")

    def test_handles_validation_error(self):
        """Test handling of validation errors."""
        with (
            patch("core.application.pipeline.core.load_file_content") as mock_load,
            patch("core.application.pipeline.core.create_extractor") as mock_create,
            patch("core.application.pipeline.core.assemble_manifest") as mock_assemble,
            patch("core.application.pipeline.core.validate_manifest") as mock_validate,
        ):
            mock_load.return_value = "content"
            mock_extractor = Mock()
            mock_extractor.extract.return_value = {"references": []}
            mock_create.return_value = mock_extractor
            mock_assemble.return_value = {"manifestId": "test"}
            mock_validate.side_effect = ValueError("Invalid manifest")

            with pytest.raises(ValueError, match="Invalid manifest"):
                build_manifest_from_file("/path/file.txt", "/tmp")


class TestCoreModule:
    """Integration tests for the core module."""

    def test_module_exports_correct_functions(self):
        """Test that module exports the expected functions."""
        from core.application.pipeline.core import (
            build_manifest_from_file,
            build_manifest_from_text,
            line,
            summary_panel,
        )

        # All functions should be callable
        assert callable(build_manifest_from_text)
        assert callable(build_manifest_from_file)
        assert callable(line)
        assert callable(summary_panel)

    @patch("core.application.pipeline.core.render_report_and_end")
    @patch("core.application.pipeline.core.write_manifest")
    @patch("core.application.pipeline.core.validate_manifest")
    @patch("core.application.pipeline.core.assemble_manifest")
    @patch("core.application.pipeline.core.create_extractor")
    @patch("core.application.pipeline.core.load_text_content")
    def test_full_pipeline_integration(
        self,
        mock_load,
        mock_create,
        mock_assemble,
        mock_validate,
        mock_write,
        mock_render,
    ):
        """Test full pipeline integration."""
        # Setup realistic mocks
        mock_load.return_value = "This is test content with https://example.com"

        mock_extractor = Mock()
        mock_extractor.extract.return_value = {
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
        mock_create.return_value = mock_extractor

        mock_manifest = {
            "manifestVersion": "1.0.0",
            "status": "Awaiting Consolidation",
            "manifestId": "integration-test-id",
            "processedAt": "2023-01-01T00:00:00Z",
            "sourceDocument": {
                "type": "text",
                "format": "text",
                "content": "This is test content with https://example.com",
            },
            "knowledgeIndex": {
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
            },
        }
        mock_assemble.return_value = mock_manifest

        # Execute pipeline
        result = build_manifest_from_text("test content", "/tmp/integration")

        # Verify complete flow executed
        mock_load.assert_called_once()
        mock_create.assert_called_once()
        mock_extractor.extract.assert_called_once()
        mock_assemble.assert_called_once()
        mock_validate.assert_called_once()
        mock_write.assert_called_once()

        assert result == mock_manifest
