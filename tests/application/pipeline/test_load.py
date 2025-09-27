"""Tests for the load module."""

from __future__ import annotations

import pytest

from core.application.pipeline.load import load_file_content, load_text_content


class TestLoadTextContent:
    """Tests for load_text_content function."""

    def test_loads_simple_text(self):
        """Test loading simple text content."""
        text = "This is a simple text."
        result = load_text_content(text)
        assert result == text

    def test_loads_empty_text(self):
        """Test loading empty text."""
        text = ""
        result = load_text_content(text)
        assert result == ""

    def test_loads_multiline_text(self):
        """Test loading multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        result = load_text_content(text)
        assert result == text

    def test_loads_text_with_special_chars(self):
        """Test loading text with special characters."""
        text = "Text with áçéñts and émojis 🚀"
        result = load_text_content(text)
        assert result == text


class TestLoadFileContent:
    """Tests for load_file_content function."""

    def test_loads_text_file(self, tmp_path):
        """Test loading a text file."""
        test_file = tmp_path / "test.txt"
        content = "Test file content"
        test_file.write_text(content, encoding="utf-8")

        result = load_file_content(str(test_file))
        assert result == content

    def test_loads_markdown_file(self, tmp_path):
        """Test loading a markdown file."""
        test_file = tmp_path / "test.md"
        content = "# Test Markdown\n\nWith some content."
        test_file.write_text(content, encoding="utf-8")

        result = load_file_content(str(test_file))

        assert "Test Markdown" in result
        assert "With some content." in result

    def test_loads_nonexistent_file(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_file_content("nonexistent_file.txt")

    def test_loads_empty_file(self, tmp_path):
        """Test loading an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        result = load_file_content(str(test_file))
        assert result == ""

    def test_loads_file_with_unicode(self, tmp_path):
        """Test loading a file with unicode content."""
        test_file = tmp_path / "unicode.txt"
        content = "Content with unicode: áéíóú, çñ, 你好"
        test_file.write_text(content, encoding="utf-8")

        result = load_file_content(str(test_file))
        assert result == content


class TestLoadModule:
    """Integration tests for the load module."""

    def test_load_functions_are_independent(self, tmp_path):
        """Test that text and file loading functions are independent."""
        # Test text loading
        text_content = "Direct text content"
        text_result = load_text_content(text_content)

        # Test file loading
        test_file = tmp_path / "test.txt"
        file_content = "File content different from text"
        test_file.write_text(file_content, encoding="utf-8")
        file_result = load_file_content(str(test_file))

        # Both should work independently
        assert text_result == text_content
        assert file_result == file_content
        assert text_result != file_result
