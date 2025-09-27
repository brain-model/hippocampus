"""Template rendering and reporting module.

This module handles template rendering and console reporting for the pipeline:
- Template rendering with Jinja2
- Console output formatting
- Pipeline phase reporting (begin, load, extract, summary, end)
- Verbose and non-verbose output modes
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

from core.resources.templates import render_template
from core.ui.console import friendly_ts, line, summary_panel

from .metrics import log_pipeline_metrics

# Template constants
_TPL_BEGIN = "cli/begin_generic.j2"
_TPL_LOAD = "cli/phase_load_generic.j2"
_TPL_EXTRACT = "cli/phase_extract_generic.j2"
_TPL_SUMMARY = "cli/summary_generic.j2"
_TPL_END = "cli/end_generic.j2"
_TPL_REPORT = "cli/report_generic.j2"


def render_report_and_end(
    verbose: bool,
    mode: str,
    extractor: Any,
    url_count: int,
    citation_count: int,
    refs_len: int,
    total_latency: int,
    manifest: dict[str, Any],
):
    """Render the final report and end message.

    Args:
        verbose: Whether verbose mode is enabled
        mode: Extraction mode
        extractor: The extractor instance with metrics
        url_count: Number of web link references
        citation_count: Number of citation references
        refs_len: Total reference count
        total_latency: Total pipeline latency in milliseconds
        manifest: The complete manifest dictionary
    """
    # Log detailed metrics if requested
    log_pipeline_metrics(
        verbose,
        mode,
        extractor,
        url_count,
        citation_count,
        refs_len,
        total_latency,
        manifest["manifestId"],
    )

    report = render_template(
        _TPL_REPORT,
        mode=mode,
        url_count=url_count,
        citation_count=citation_count,
        total_refs=refs_len,
        total_ms=total_latency,
        manifest_id=manifest["manifestId"],
        processed_friendly=friendly_ts(manifest["processedAt"]),
        provider=getattr(extractor, "last_provider", None) if mode == "llm" else None,
        model=getattr(extractor, "last_model", None) if mode == "llm" else None,
        tokens=getattr(extractor, "last_tokens", None) if mode == "llm" else None,
        llm_latency_ms=(
            getattr(extractor, "last_extract_latency_ms", None)
            if mode == "llm"
            else None
        ),
        graph_total_ms=(
            getattr(extractor, "last_graph_total_ms", None) if mode == "llm" else None
        ),
        graph_tokens=(
            getattr(extractor, "last_graph_tokens", None) if mode == "llm" else None
        ),
    )
    if verbose:
        summary_panel("Collect Report", report)
    else:
        line(report)
    line(
        render_template(
            _TPL_END,
            mode=mode,
            manifest_id=manifest["manifestId"],
            url_count=url_count,
            citation_count=citation_count,
            total_refs=refs_len,
            processed_at=manifest["processedAt"],
            latency_ms=total_latency,
        )
    )


def log_begin(
    mode: str,
    source_type: str,
    source_format: str,
    resolved_cfg: dict[str, Any],
    provenance: dict[str, str],
) -> None:
    """Log the beginning of pipeline execution.

    Args:
        mode: Extraction mode
        source_type: Type of source document
        source_format: Format of source document
        resolved_cfg: Resolved engine configuration
        provenance: Configuration provenance information
    """
    line(f"begin={mode} | source={source_type} | format={source_format}")
    if mode == "llm" and resolved_cfg:
        prov = ", ".join(
            f"{k}({provenance.get(k)})={v}" for k, v in resolved_cfg.items()
        )
        line(f"engine: {prov}")


def extract_with_timing(extractor: Any, normalized: str, mode: str) -> tuple[dict, int]:
    """Extract references with timing measurement.

    Args:
        extractor: The extractor instance
        normalized: Normalized content to process
        mode: Extraction mode

    Returns:
        Tuple of (extracted_data, latency_ms)
    """
    start = time.time()
    extracted = extractor.extract(normalized)
    latency = int((time.time() - start) * 1000)
    if mode == "llm" and getattr(extractor, "last_extract_latency_ms", None) is None:
        with contextlib.suppress(Exception):
            extractor.last_extract_latency_ms = latency
    return extracted, latency


def render_load_phase(
    mode: str,
    loader_name: str,
    latency_ms: int,
    char_count: int,
) -> None:
    """Render the load phase report.

    Args:
        mode: Extraction mode
        loader_name: Name of the loader class used
        latency_ms: Load latency in milliseconds
        char_count: Character count of loaded content
    """
    line(
        render_template(
            _TPL_LOAD,
            mode=mode,
            loader_name=loader_name,
            latency_ms=latency_ms,
            char_count=char_count,
        )
    )


def render_extract_phase(
    mode: str,
    url_count: int,
    citation_count: int,
    total_refs: int,
    latency_ms: int,
) -> None:
    """Render the extract phase report.

    Args:
        mode: Extraction mode
        url_count: Number of web link references found
        citation_count: Number of citation references found
        total_refs: Total reference count
        latency_ms: Extraction latency in milliseconds
    """
    line(
        render_template(
            _TPL_EXTRACT,
            mode=mode,
            url_count=url_count,
            citation_count=citation_count,
            total_refs=total_refs,
            latency_ms=latency_ms,
        )
    )


def render_summary_phase(
    mode: str,
    url_count: int,
    citation_count: int,
    total_refs: int,
    latency_ms: int,
) -> None:
    """Render the summary phase report.

    Args:
        mode: Extraction mode
        url_count: Number of web link references found
        citation_count: Number of citation references found
        total_refs: Total reference count
        latency_ms: Total latency in milliseconds
    """
    line(
        render_template(
            _TPL_SUMMARY,
            mode=mode,
            url_count=url_count,
            citation_count=citation_count,
            total_refs=total_refs,
            latency_ms=latency_ms,
        )
    )


def render_begin_phase(
    mode: str,
    source_type: str,
    source_format: str,
    timestamp: str,
) -> None:
    """Render the begin phase report.

    Args:
        mode: Extraction mode
        source_type: Type of source document
        source_format: Format of source document
        timestamp: Current timestamp
    """
    line(
        render_template(
            _TPL_BEGIN,
            mode=mode,
            source_type=source_type,
            source_format=source_format,
            timestamp=timestamp,
        )
    )
