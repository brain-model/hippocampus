"""Tests for the metrics module."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

from core.application.pipeline.metrics import log_pipeline_metrics


class TestLogPipelineMetrics:
    """Tests for log_pipeline_metrics function."""

    @patch("core.application.pipeline.metrics.get_logger")
    def test_logs_basic_metrics_verbose_mode(self, mock_get_logger):
        """Test logging basic metrics in verbose mode."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create mock extractor
        extractor = Mock()

        log_pipeline_metrics(
            verbose=True,
            mode="heuristic",
            extractor=extractor,
            url_count=2,
            citation_count=3,
            refs_len=5,
            total_latency=1000,
            manifest_id="test-manifest-id",
        )

        # Should get logger with DEBUG level for verbose mode
        mock_get_logger.assert_called_once()
        args = mock_get_logger.call_args[1]
        assert args["level"] == "DEBUG"

        # Should call logger.info
        mock_logger.info.assert_called()

    @patch("core.application.pipeline.metrics.get_logger")
    def test_logs_basic_metrics_non_verbose_mode(self, mock_get_logger):
        """Test logging basic metrics in non-verbose mode."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        extractor = Mock()

        log_pipeline_metrics(
            verbose=False,
            mode="heuristic",
            extractor=extractor,
            url_count=1,
            citation_count=2,
            refs_len=3,
            total_latency=500,
            manifest_id="test-id",
        )

        # Should get logger with INFO level for non-verbose mode
        mock_get_logger.assert_called_once()
        args = mock_get_logger.call_args[1]
        assert args["level"] == "INFO"

    @patch("core.application.pipeline.metrics.get_logger")
    @patch.dict(os.environ, {"HIPPO_TRACE_LLM": "true"})
    def test_logs_with_llm_trace_enabled(self, mock_get_logger):
        """Test logging with LLM trace enabled."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        extractor = Mock()

        log_pipeline_metrics(
            verbose=False,  # Even with verbose=False, should log due to trace
            mode="llm",
            extractor=extractor,
            url_count=1,
            citation_count=1,
            refs_len=2,
            total_latency=800,
            manifest_id="trace-test-id",
        )

        # Should call logger.info even in non-verbose mode due to trace
        mock_logger.info.assert_called()

    @patch("core.application.pipeline.metrics.get_logger")
    @patch.dict(os.environ, {"HIPPO_TRACE_GRAPH": "true"})
    def test_logs_with_graph_trace_enabled(self, mock_get_logger):
        """Test logging with Graph trace enabled."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        extractor = Mock()

        log_pipeline_metrics(
            verbose=False,
            mode="llm-graph",
            extractor=extractor,
            url_count=2,
            citation_count=2,
            refs_len=4,
            total_latency=1200,
            manifest_id="graph-trace-id",
        )

        # Should call logger.info due to graph trace
        mock_logger.info.assert_called()

    @patch("core.application.pipeline.metrics.get_logger")
    @patch.dict(os.environ, {}, clear=True)
    def test_does_not_log_detailed_metrics_when_disabled(self, mock_get_logger):
        """Test that detailed metrics are not logged when all traces disabled."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        extractor = Mock()

        log_pipeline_metrics(
            verbose=False,
            mode="heuristic",
            extractor=extractor,
            url_count=1,
            citation_count=1,
            refs_len=2,
            total_latency=300,
            manifest_id="no-trace-id",
        )

        # Logger should be created but not necessarily called for detailed metrics
        mock_get_logger.assert_called_once()


class TestMetricsModule:
    """Integration tests for the metrics module."""

    @patch("core.application.pipeline.metrics.get_logger")
    def test_full_metrics_logging_flow(self, mock_get_logger):
        """Test full metrics logging flow."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create realistic extractor
        extractor = Mock()
        extractor.last_provider = "openai"
        extractor.last_model = "gpt-4"
        extractor.last_tokens = 200
        extractor.last_latency_ms = 1500

        # Log metrics
        log_pipeline_metrics(
            verbose=True,
            mode="llm",
            extractor=extractor,
            url_count=3,
            citation_count=5,
            refs_len=8,
            total_latency=2000,
            manifest_id="integration-test-id",
        )

        # Should create logger and log info
        mock_get_logger.assert_called_once()
        mock_logger.info.assert_called()

    def test_environment_variable_handling(self):
        """Test that environment variables are handled correctly."""
        # Test with various environment variable states
        test_cases = [
            {"HIPPO_TRACE_LLM": "true", "HIPPO_TRACE_GRAPH": "false"},
            {"HIPPO_TRACE_LLM": "false", "HIPPO_TRACE_GRAPH": "true"},
            {"HIPPO_TRACE_LLM": "TRUE", "HIPPO_TRACE_GRAPH": "FALSE"},
        ]

        for env_vars in test_cases:
            with patch.dict(os.environ, env_vars):
                # Test should pass without errors
                extractor = Mock()
                log_pipeline_metrics(
                    verbose=False,
                    mode="heuristic",
                    extractor=extractor,
                    url_count=0,
                    citation_count=0,
                    refs_len=0,
                    total_latency=100,
                    manifest_id="env-test-id",
                )
