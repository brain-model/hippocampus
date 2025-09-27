"""Reference extraction module with unified interface.

This module provides adapters for different extraction engines:
- Heuristic extraction (deterministic, fast)
- LLM extraction (LangChain-based, configurable providers)
- Graph extraction (LangGraph orchestration with fallback)
"""

from __future__ import annotations

import time
from typing import Any

from core.infrastructure.config.resolver import resolve_engine_config
from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent
from core.noesis.graph.types import GraphConfig


class GraphExtractorAdapter:
    """Adapter for LangGraph-based extraction with metrics tracking."""

    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.last_provider = None
        self.last_model = None
        self.last_tokens = None  # tokens from LLM extraction step, when available
        self.last_extract_latency_ms = None
        self.last_graph_total_ms = None
        self.last_graph_tokens = None

    def extract(self, text: str) -> dict:
        """Extract references using the graph orchestrator.

        Args:
            text: Input text to extract references from

        Returns:
            Dictionary containing extracted references
        """
        from core.noesis.graph.agent import GraphOrchestrator

        t0 = time.time()
        out = GraphOrchestrator(self.cfg).run(text)
        self.last_extract_latency_ms = int((time.time() - t0) * 1000)
        m = out.get("metrics") or {}
        toks = m.get("total_tokens") if isinstance(m, dict) else None
        if isinstance(toks, dict):
            self.last_graph_tokens = toks
        total_ms = m.get("total_latency_ms") if isinstance(m, dict) else None
        if isinstance(total_ms, int):
            self.last_graph_total_ms = total_ms
        # Prefer real LLM provider/model if present
        if isinstance(out.get("llm"), dict):
            self.last_provider = out["llm"].get("provider") or None
            self.last_model = out["llm"].get("model") or None
        else:
            # Fallback identifiers for graph mode
            self.last_provider = self.last_provider or "graph"
            self.last_model = self.last_model or "llm-graph"
        # If extract node provided per-step tokens, surface them as last_tokens
        # Here we only have totals; keep last_tokens None to avoid ambiguity
        return {"references": out.get("references", [])}


def create_extractor(
    engine: str,
    engine_overrides: dict[str, Any] | None = None,
    graph_config: Any | None = None,
) -> Any:
    """Create an appropriate extractor based on the engine type.

    Args:
        engine: Engine type ('heuristic', 'llm', 'llm-graph')
        engine_overrides: Configuration overrides for the engine
        graph_config: Graph-specific configuration for llm-graph mode

    Returns:
        Configured extractor instance
    """
    mode = get_engine_mode(engine)
    use_graph = engine == "llm-graph"

    if mode == "heuristic":
        return HeuristicExtractionAgent()

    # LLM mode
    resolved_cfg, _ = resolve_engine_config(engine_overrides or {})

    from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent

    if use_graph:
        return _create_graph_extractor(resolved_cfg, graph_config)
    return LangChainExtractionAgent(cfg_override=resolved_cfg)


def _create_graph_extractor(
    resolved_cfg: dict[str, Any], graph_config: Any | None
) -> GraphExtractorAdapter:
    """Create a graph extractor with proper configuration.

    Args:
        resolved_cfg: Resolved LLM configuration
        graph_config: Graph-specific configuration

    Returns:
        Configured GraphExtractorAdapter instance
    """
    cfg = GraphConfig(enabled=True)
    if graph_config:
        # best-effort copy of attributes
        for attr in (
            "use_fallback",
            "timeout_s",
            "retries",
            "backoff_base_s",
            "backoff_max_s",
            "jitter_s",
        ):
            if hasattr(graph_config, attr):
                setattr(cfg, attr, getattr(graph_config, attr))
    cfg.engine_overrides = resolved_cfg
    return GraphExtractorAdapter(cfg)


def get_engine_mode(engine: str) -> str:
    """Get the normalized mode name for an engine.

    Args:
        engine: Engine type

    Returns:
        Normalized mode name ('heuristic', 'llm', or 'llm-graph')
    """
    if engine == "llm-graph":
        return "llm"
    if engine in {"heuristic", "llm"}:
        return engine
    return "heuristic"
