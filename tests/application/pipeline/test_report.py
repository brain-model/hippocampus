"""Tests for the report module."""

from __future__ import annotations

import time
from unittest.mock import Mock, patch

from core.application.pipeline.report import (
    extract_with_timing,
    render_begin_phase,
    render_extract_phase,
    render_load_phase,
    render_report_and_end,
    render_summary_phase,
)


class TestRenderBeginPhase:
    """Tests for render_begin_phase function."""

    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.line")
    def test_renders_begin_phase_basic(self, mock_line, mock_render):
        """Test rendering basic begin phase."""
        mock_render.return_value = "begin output"

        render_begin_phase(
            mode="heuristic",
            source_type="text",
            source_format="text",
            timestamp="2023-01-01T00:00:00Z",
        )

        # Should render template and output line
        mock_render.assert_called_once()
        mock_line.assert_called_once_with("begin output")

    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.line")
    def test_renders_begin_phase_with_file(self, mock_line, mock_render):
        """Test rendering begin phase with file input."""
        mock_render.return_value = "begin file output"

        render_begin_phase(
            mode="llm",
            source_type="file",
            source_format="md",
            timestamp="2023-01-01T00:00:00Z",
        )

        mock_render.assert_called_once()
        # Check template call arguments
        args = mock_render.call_args[1]
        assert args["mode"] == "llm"
        assert args["source_type"] == "file"
        assert args["source_format"] == "md"


class TestRenderLoadPhase:
    """Tests for render_load_phase function."""

    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.line")
    def test_renders_load_phase(self, mock_line, mock_render):
        """Test rendering load phase."""
        mock_render.return_value = "load output"

        render_load_phase(
            mode="heuristic", loader_name="TextLoader", latency_ms=100, char_count=500
        )

        mock_render.assert_called_once()
        mock_line.assert_called_once_with("load output")

        # Check template arguments
        args = mock_render.call_args[1]
        assert args["mode"] == "heuristic"
        assert args["loader_name"] == "TextLoader"
        assert args["latency_ms"] == 100
        assert args["char_count"] == 500


class TestRenderExtractPhase:
    """Tests for render_extract_phase function."""

    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.line")
    def test_renders_extract_phase(self, mock_line, mock_render):
        """Test rendering extract phase."""
        mock_render.return_value = "extract output"

        render_extract_phase(
            mode="heuristic",
            url_count=2,
            citation_count=3,
            total_refs=5,
            latency_ms=200,
        )

        mock_render.assert_called_once()
        mock_line.assert_called_once_with("extract output")

        # Check template arguments
        args = mock_render.call_args[1]
        assert args["mode"] == "heuristic"
        assert args["url_count"] == 2
        assert args["citation_count"] == 3
        assert args["total_refs"] == 5
        assert args["latency_ms"] == 200


class TestRenderSummaryPhase:
    """Tests for render_summary_phase function."""

    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.line")
    def test_renders_summary_phase(self, mock_line, mock_render):
        """Test rendering summary phase."""
        mock_render.return_value = "summary output"

        render_summary_phase(
            mode="llm", url_count=1, citation_count=2, total_refs=3, latency_ms=1500
        )

        mock_render.assert_called_once()
        mock_line.assert_called_once_with("summary output")

        # Check template arguments
        args = mock_render.call_args[1]
        assert args["mode"] == "llm"
        assert args["url_count"] == 1
        assert args["citation_count"] == 2
        assert args["total_refs"] == 3
        assert args["latency_ms"] == 1500


class TestRenderReportAndEnd:
    """Tests for render_report_and_end function."""

    @patch("core.application.pipeline.report.log_pipeline_metrics")
    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.summary_panel")
    def test_renders_report_verbose_mode(self, mock_panel, mock_render, mock_log):
        """Test rendering report in verbose mode."""
        mock_render.return_value = "end template output"
        extractor = Mock()
        manifest = {"manifestId": "test-id", "processedAt": "2024-01-01T00:00:00Z"}

        render_report_and_end(
            verbose=True,
            mode="heuristic",
            extractor=extractor,
            url_count=2,
            citation_count=3,
            refs_len=5,
            total_latency=1000,
            manifest=manifest,
        )

        # Should render template and show summary panel
        assert mock_render.call_count == 2  # Called twice: report + end templates
        mock_panel.assert_called_once()

        # Should log metrics
        mock_log.assert_called_once_with(
            True, "heuristic", extractor, 2, 3, 5, 1000, "test-id"
        )

    @patch("core.application.pipeline.report.log_pipeline_metrics")
    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.summary_panel")
    def test_renders_report_non_verbose_mode(self, mock_panel, mock_render, mock_log):
        """Test rendering report in non-verbose mode."""
        mock_render.return_value = "end template output"
        extractor = Mock()
        manifest = {"manifestId": "test-id", "processedAt": "2024-01-01T00:00:00Z"}

        render_report_and_end(
            verbose=False,
            mode="llm",
            extractor=extractor,
            url_count=1,
            citation_count=1,
            refs_len=2,
            total_latency=800,
            manifest=manifest,
        )

        # Should render template but use line() instead of summary_panel()
        assert mock_render.call_count == 2  # Called twice: report + end templates
        mock_panel.assert_not_called()  # Should not show panel in non-verbose mode

        # Should still log metrics
        mock_log.assert_called_once_with(
            False, "llm", extractor, 1, 1, 2, 800, "test-id"
        )


class TestExtractWithTiming:
    """Tests for extract_with_timing function."""

    def test_times_extraction_correctly(self):
        """Test that extraction timing works correctly."""
        # Create mock extractor that takes some time
        extractor = Mock()

        def slow_extract(text):
            time.sleep(0.01)  # 10ms
            return {"references": []}

        extractor.extract = slow_extract

        result, latency = extract_with_timing(extractor, "test text", "heuristic")

        # Should return result and timing
        assert result == {"references": []}
        assert latency >= 10  # Should be at least 10ms
        assert latency < 1000  # Should be reasonable (less than 1 second)

    def test_handles_extraction_error(self):
        """Test handling extraction errors with timing."""
        extractor = Mock()
        extractor.extract.side_effect = RuntimeError("Extraction failed")

        # Should re-raise the error
        try:
            extract_with_timing(extractor, "test text", "heuristic")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert str(e) == "Extraction failed"

    def test_times_fast_extraction(self):
        """Test timing very fast extractions."""
        extractor = Mock()
        extractor.extract.return_value = {"references": [{"id": 1}]}

        result, latency = extract_with_timing(extractor, "test", "heuristic")

        assert result == {"references": [{"id": 1}]}
        assert latency >= 0  # Should be non-negative
        assert isinstance(latency, int)  # Should be integer milliseconds


class TestReportModule:
    """Integration tests for the report module."""

    @patch("core.application.pipeline.report.render_template")
    @patch("core.application.pipeline.report.line")
    def test_all_phases_render_correctly(self, mock_line, mock_render):
        """Test that all phases can be rendered in sequence."""
        mock_render.return_value = "template output"

        # Render all phases
        render_begin_phase("heuristic", "text", "text", "2023-01-01T00:00:00Z")
        render_load_phase("heuristic", "TextLoader", 100, 500)
        render_extract_phase("heuristic", 1, 2, 3, 200)
        render_summary_phase("heuristic", 1, 2, 3, 1000)

        # Should call render_template for each phase
        assert mock_render.call_count == 4
        assert mock_line.call_count == 4

    @patch("core.application.pipeline.report.log_pipeline_metrics")
    def test_end_phase_always_logs_metrics(self, mock_log):
        """Test that end phase always logs metrics regardless of verbose mode."""
        extractor = Mock()
        manifest = {"manifestId": "test-id", "processedAt": "2024-01-01T00:00:00Z"}

        # Test both verbose modes
        for verbose in [True, False]:
            mock_log.reset_mock()

            render_report_and_end(
                verbose=verbose,
                mode="heuristic",
                extractor=extractor,
                url_count=0,
                citation_count=0,
                refs_len=0,
                total_latency=100,
                manifest=manifest,
            )

            # Should always log metrics
            mock_log.assert_called_once()
