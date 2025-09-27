"""Metrics aggregation and logging module.

This module handles the collection, aggregation and logging of pipeline metrics:
- Pipeline execution metrics (latency, reference counts)
- LLM-specific metrics (provider, model, tokens, latency)
- Graph-specific metrics (total latency, token aggregation)
- Structured logging with trace support
"""

from __future__ import annotations

import os
from typing import Any

from core.infrastructure.logging.structured import get_logger


def log_pipeline_metrics(
    verbose: bool,
    mode: str,
    extractor: Any,
    url_count: int,
    citation_count: int,
    refs_len: int,
    total_latency: int,
    manifest_id: str,
):
    """Log detailed pipeline metrics if verbose or traces enabled.

    Args:
        verbose: Whether verbose logging is enabled
        mode: Extraction mode ('heuristic', 'llm', 'llm-graph')
        extractor: The extractor instance with metrics
        url_count: Number of web link references found
        citation_count: Number of citation references found
        refs_len: Total number of references
        total_latency: Total pipeline latency in milliseconds
        manifest_id: The manifest ID for correlation
    """
    logger = get_logger(__name__, level="DEBUG" if verbose else "INFO")

    # Check for trace environment variables
    trace_llm = os.getenv("HIPPO_TRACE_LLM", "false").lower() == "true"
    trace_graph = os.getenv("HIPPO_TRACE_GRAPH", "false").lower() == "true"

    # Log detailed metrics if verbose or traces enabled
    if verbose or trace_llm or trace_graph:
        logger.info(
            "Pipeline execution completed",
            mode=mode,
            url_count=url_count,
            citation_count=citation_count,
            total_refs=refs_len,
            total_latency_ms=total_latency,
            manifest_id=manifest_id,
        )

        # Log LLM details if available and traces enabled
        if mode == "llm" and (verbose or trace_llm):
            log_llm_details(logger, extractor)

        # Log Graph details if available and traces enabled
        if mode == "llm-graph" and (verbose or trace_graph):
            log_graph_details(logger, extractor)


def log_llm_details(logger, extractor: Any):
    """Log LLM execution details.

    Args:
        logger: The logger instance to use
        extractor: The LLM extractor with metrics attributes
    """
    provider = getattr(extractor, "last_provider", None)
    model = getattr(extractor, "last_model", None)
    tokens = getattr(extractor, "last_tokens", None)
    llm_latency = getattr(extractor, "last_extract_latency_ms", None)

    if provider:
        logger.info(
            "LLM execution details",
            provider=provider,
            model=model,
            tokens=tokens,
            llm_latency_ms=llm_latency,
        )


def log_graph_details(logger, extractor: Any):
    """Log Graph execution details.

    Args:
        logger: The logger instance to use
        extractor: The graph extractor with metrics attributes
    """
    graph_total_ms = getattr(extractor, "last_graph_total_ms", None)
    graph_tokens = getattr(extractor, "last_graph_tokens", None)

    if graph_total_ms is not None:
        logger.info(
            "Graph execution details",
            graph_total_ms=graph_total_ms,
            graph_tokens=graph_tokens,
        )
