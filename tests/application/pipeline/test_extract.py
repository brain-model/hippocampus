"""Tests for the extract module."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from core.application.pipeline.extract import (
    GraphExtractorAdapter,
    create_extractor,
    get_engine_mode,
)


class TestGetEngineMode:
    """Tests for get_engine_mode function."""

    def test_heuristic_engine(self):
        """Test heuristic engine mode."""
        assert get_engine_mode("heuristic") == "heuristic"

    def test_llm_engine(self):
        """Test LLM engine mode."""
        assert get_engine_mode("llm") == "llm"

    def test_llm_graph_engine(self):
        """Test LLM-graph engine mode."""
        assert get_engine_mode("llm-graph") == "llm"

    def test_unknown_engine_defaults_to_heuristic(self):
        """Test that unknown engine defaults to heuristic."""
        assert get_engine_mode("unknown") == "heuristic"

    def test_empty_engine_defaults_to_heuristic(self):
        """Test that empty engine defaults to heuristic."""
        assert get_engine_mode("") == "heuristic"


class TestCreateExtractor:
    """Tests for create_extractor function."""

    def test_creates_heuristic_extractor(self):
        """Test creating heuristic extractor."""
        extractor = create_extractor("heuristic")

        # Should be HeuristicExtractionAgent
        assert hasattr(extractor, "extract")
        assert extractor.__class__.__name__ == "HeuristicExtractionAgent"

    @patch("core.application.pipeline.extract.resolve_engine_config")
    @patch("core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent")
    def test_creates_llm_extractor(self, mock_agent, mock_resolve):
        """Test creating LLM extractor."""
        # Mock dependencies
        mock_resolve.return_value = ({"provider": "openai"}, {"provider": "default"})
        mock_instance = Mock()
        mock_agent.return_value = mock_instance

        extractor = create_extractor("llm", {"provider": "openai"})

        # Should resolve config and create LangChain agent
        mock_resolve.assert_called_once_with({"provider": "openai"})
        mock_agent.assert_called_once_with(cfg_override={"provider": "openai"})
        assert extractor == mock_instance

    @patch("core.application.pipeline.extract.resolve_engine_config")
    @patch("core.application.pipeline.extract._create_graph_extractor")
    def test_creates_llm_graph_extractor(self, mock_create_graph, mock_resolve):
        """Test creating LLM-graph extractor."""
        # Mock dependencies
        mock_resolve.return_value = ({"provider": "openai"}, {"provider": "default"})
        mock_graph_extractor = Mock()
        mock_create_graph.return_value = mock_graph_extractor

        graph_config = {"max_depth": 3}
        extractor = create_extractor("llm-graph", {"provider": "openai"}, graph_config)

        # Should resolve config and create graph extractor
        mock_resolve.assert_called_once_with({"provider": "openai"})
        mock_create_graph.assert_called_once_with({"provider": "openai"}, graph_config)
        assert extractor == mock_graph_extractor

    def test_creates_heuristic_with_overrides_ignored(self):
        """Test creating heuristic extractor ignores config overrides."""
        extractor = create_extractor("heuristic", {"provider": "openai"})

        # Should still create heuristic extractor, ignoring overrides
        assert extractor.__class__.__name__ == "HeuristicExtractionAgent"


class TestGraphExtractorAdapter:
    """Tests for GraphExtractorAdapter class."""

    def test_initialization(self):
        """Test GraphExtractorAdapter initialization."""
        cfg = {"provider": "openai", "model": "gpt-4"}
        adapter = GraphExtractorAdapter(cfg)

        assert adapter.cfg == cfg
        assert adapter.last_provider is None
        assert adapter.last_model is None
        assert adapter.last_tokens is None
        assert adapter.last_extract_latency_ms is None
        assert adapter.last_graph_total_ms is None
        assert adapter.last_graph_tokens is None

    @patch("core.noesis.graph.agent.GraphOrchestrator")
    def test_extract_method_exists(self, mock_orchestrator_class):
        """Test that GraphExtractorAdapter has extract method."""
        cfg = {"provider": "openai"}
        adapter = GraphExtractorAdapter(cfg)

        # Should have extract method
        assert hasattr(adapter, "extract")
        assert callable(adapter.extract)

    @patch("core.noesis.graph.agent.GraphOrchestrator")
    def test_extract_calls_graph(self, mock_orchestrator_class):
        """Test that extract method calls the graph."""
        # Mock the orchestrator instance and return value
        mock_orchestrator = Mock()
        mock_orchestrator.run.return_value = {
            "references": [{"id": 1, "rawString": "test"}],
            "metrics": {
                "total_tokens": {"completion": 50, "prompt": 50},
                "total_latency_ms": 1000,
            },
            "llm": {"provider": "openai", "model": "gpt-4"},
        }
        mock_orchestrator_class.return_value = mock_orchestrator

        cfg = {"provider": "openai"}
        adapter = GraphExtractorAdapter(cfg)

        result = adapter.extract("test content")

        # Should create orchestrator and call run method
        mock_orchestrator_class.assert_called_once_with(cfg)
        mock_orchestrator.run.assert_called_once_with("test content")

        # Should track metrics correctly from response
        assert adapter.last_provider == "openai"
        assert adapter.last_model == "gpt-4"
        assert adapter.last_graph_tokens == {"completion": 50, "prompt": 50}
        assert adapter.last_graph_total_ms == 1000
        assert adapter.last_extract_latency_ms is not None  # Set by timing

        assert result == {"references": [{"id": 1, "rawString": "test"}]}


class TestExtractModule:
    """Integration tests for the extract module."""

    def test_heuristic_extraction_end_to_end(self):
        """Test heuristic extraction from start to finish."""
        extractor = create_extractor("heuristic")

        # Test content with references
        text = "See https://example.com and (Smith, 2020)"
        result = extractor.extract(text)

        # Should extract references
        assert "references" in result
        assert len(result["references"]) >= 1  # At least the URL should be found

    @patch("core.application.pipeline.extract.resolve_engine_config")
    def test_extraction_error_handling(self, mock_resolve):
        """Test that extraction handles errors gracefully."""
        # Mock config resolution to raise an error
        mock_resolve.side_effect = RuntimeError("Config error")

        # Should handle the error when creating LLM extractor
        with pytest.raises(RuntimeError, match="Config error"):
            create_extractor("llm", {"provider": "invalid"})
