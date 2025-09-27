"""Core pipeline implementation using refactored modules.

This module implements the main pipeline functions using the clean separation
of concerns provided by the sub-modules.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.infrastructure.config.resolver import resolve_engine_config
from core.ui.console import collect_section, progress_bar

from .assemble import assemble_manifest, count_references_by_type
from .extract import create_extractor, get_engine_mode
from .io import write_manifest
from .load import load_file_content, load_text_content
from .report import (
    extract_with_timing,
    render_begin_phase,
    render_extract_phase,
    render_load_phase,
    render_report_and_end,
    render_summary_phase,
)
from .validate import validate_manifest

# Schema file constants
SCHEMA_FILENAME = "manifest.schema.json"


def _get_schema_path() -> str:
    """Get the path to the manifest schema file."""
    base_path = Path(__file__).parent.parent.parent
    return str(base_path / "resources" / "schemas" / SCHEMA_FILENAME)


# Wrapper functions for test compatibility
def line(message: str) -> None:
    """Wrapper for ui.console.line function that can be mocked in tests."""
    from core.ui.console import line as console_line

    console_line(message)


def summary_panel(title: str, content: str) -> None:
    """Wrapper for ui.console.summary_panel function that can be mocked in tests."""
    from core.ui.console import summary_panel as console_summary_panel

    console_summary_panel(title, content)


def build_manifest_from_text(
    text: str,
    out_dir: str,
    verbose: bool = False,
    engine: str = "heuristic",
    engine_overrides: dict[str, Any] | None = None,
    graph_config: Any | None = None,
) -> dict[str, Any]:
    """Build and persist a manifest from input text.

    The flow loads and normalizes the text, extracts references, assembles
    the manifest dictionary, validates it against the JSON Schema, and writes
    the resulting JSON file to disk.

    Args:
        text: Input content to be indexed and analyzed.
        out_dir: Base directory where the JSON will be saved (subfolder `manifest`).
        verbose: Enable verbose logging and UI
        engine: Extraction engine ('heuristic', 'llm', 'llm-graph')
        engine_overrides: Configuration overrides for the engine
        graph_config: Graph-specific configuration for llm-graph mode

    Returns:
        The validated manifest dictionary persisted on disk.

    Raises:
        ValueError: If schema validation fails.
        OSError: If directory creation or file writing fails.
    """
    mode = get_engine_mode(engine)

    # Resolve configuration for LLM modes
    if mode == "llm":
        resolved_cfg, provenance = resolve_engine_config(engine_overrides or {})
    else:
        resolved_cfg, provenance = {}, {}

    # Create extractor
    extractor = create_extractor(engine, engine_overrides, graph_config)

    if not verbose:
        with collect_section("Collect"):
            # Beginning phase
            render_begin_phase(
                mode,
                "text",
                "text",
                datetime.now(UTC).isoformat(),
            )

            t0 = time.time()
            with progress_bar(["load", "extract"]) as (prog, tasks):
                normalized = load_text_content(text)
                prog.update(tasks["load"], advance=1)
                extracted = extractor.extract(normalized)
                prog.update(tasks["extract"], advance=1)
            total_latency = int((time.time() - t0) * 1000)

            refs = extracted.get("references", [])
            url_count, citation_count, total_refs = count_references_by_type(refs)

            render_summary_phase(
                mode,
                url_count,
                citation_count,
                total_refs,
                total_latency,
            )
    else:
        # Verbose mode with streaming logs
        t0 = time.time()
        # Log begin phase - replicated here for test compatibility
        line(f"begin={mode} | source=text | format=text")
        if mode == "llm" and resolved_cfg:
            prov = ", ".join(
                f"{k}({provenance.get(k)})={v}" for k, v in resolved_cfg.items()
            )
            line(f"engine: {prov}")

        load_start = time.time()
        normalized = load_text_content(text)
        load_latency = int((time.time() - load_start) * 1000)

        render_load_phase(
            mode,
            "TextLoader",  # Always TextLoader for text input
            load_latency,
            len(normalized or ""),
        )

        extracted, extract_latency = extract_with_timing(extractor, normalized, mode)

        refs = extracted.get("references", [])
        url_count, citation_count, total_refs = count_references_by_type(refs)

        render_extract_phase(
            mode,
            url_count,
            citation_count,
            total_refs,
            extract_latency,
        )

        total_latency = int((time.time() - t0) * 1000)

        render_summary_phase(
            mode,
            url_count,
            citation_count,
            total_refs,
            total_latency,
        )

    # Assemble manifest
    manifest = assemble_manifest(normalized, extracted, "text", "text")

    # Validate manifest
    validate_manifest(manifest, _get_schema_path())

    # Render final report
    refs = extracted.get("references", [])
    url_count, citation_count, total_refs = count_references_by_type(refs)

    render_report_and_end(
        verbose,
        mode,
        extractor,
        url_count,
        citation_count,
        total_refs,
        total_latency,
        manifest,
    )

    # Write to disk
    write_manifest(manifest, out_dir)

    return manifest


def build_manifest_from_file(
    file_path: str,
    out_dir: str,
    verbose: bool = False,
    engine: str = "heuristic",
    engine_overrides: dict[str, Any] | None = None,
    graph_config: Any | None = None,
) -> dict[str, Any]:
    """Build and persist a manifest from an input file.

    Selects an appropriate loader based on the file extension, normalizes
    the content, extracts references, assembles the manifest, validates it
    and writes the resulting JSON file to disk.

    Args:
        file_path: Path to the input file.
        out_dir: Base directory where the JSON will be saved.
        verbose: Enable verbose logging and UI
        engine: Extraction engine ('heuristic', 'llm', 'llm-graph')
        engine_overrides: Configuration overrides for the engine
        graph_config: Graph-specific configuration for llm-graph mode

    Returns:
        The validated manifest dictionary persisted on disk.

    Raises:
        ValueError: If schema validation fails.
        OSError: If file reading or writing fails.
    """
    from pathlib import Path

    mode = get_engine_mode(engine)

    # Resolve configuration for LLM modes
    if mode == "llm":
        resolved_cfg, provenance = resolve_engine_config(engine_overrides or {})
    else:
        resolved_cfg, provenance = {}, {}

    # Create extractor
    extractor = create_extractor(engine, engine_overrides, graph_config)

    # Determine source format from file extension
    path = Path(file_path)
    source_format = path.suffix.lstrip(".") or "unknown"

    if not verbose:
        with collect_section("Collect"):
            # Beginning phase
            render_begin_phase(
                mode,
                "file",
                source_format,
                datetime.now(UTC).isoformat(),
            )

            t0 = time.time()
            with progress_bar(["load", "extract"]) as (prog, tasks):
                normalized = load_file_content(file_path)
                prog.update(tasks["load"], advance=1)
                extracted = extractor.extract(normalized)
                prog.update(tasks["extract"], advance=1)
            total_latency = int((time.time() - t0) * 1000)

            refs = extracted.get("references", [])
            url_count, citation_count, total_refs = count_references_by_type(refs)

            render_summary_phase(
                mode,
                url_count,
                citation_count,
                total_refs,
                total_latency,
            )
    else:
        # Verbose mode with streaming logs
        t0 = time.time()
        # Log begin phase - replicated here for test compatibility
        line(f"begin={mode} | source=file | format={source_format}")
        if mode == "llm" and resolved_cfg:
            prov = ", ".join(
                f"{k}({provenance.get(k)})={v}" for k, v in resolved_cfg.items()
            )
            line(f"engine: {prov}")

        load_start = time.time()
        normalized = load_file_content(file_path)
        load_latency = int((time.time() - load_start) * 1000)

        from core.infrastructure.loaders.registry import get_loader_for_file

        loader = get_loader_for_file(file_path)
        loader_name = type(loader).__name__

        render_load_phase(
            mode,
            loader_name,
            load_latency,
            len(normalized or ""),
        )

        extracted, extract_latency = extract_with_timing(extractor, normalized, mode)

        refs = extracted.get("references", [])
        url_count, citation_count, total_refs = count_references_by_type(refs)

        render_extract_phase(
            mode,
            url_count,
            citation_count,
            total_refs,
            extract_latency,
        )

        total_latency = int((time.time() - t0) * 1000)

        render_summary_phase(
            mode,
            url_count,
            citation_count,
            total_refs,
            total_latency,
        )

    # Assemble manifest
    manifest = assemble_manifest(normalized, extracted, "file", source_format)

    # Validate manifest
    validate_manifest(manifest, _get_schema_path())

    # Render final report
    refs = extracted.get("references", [])
    url_count, citation_count, total_refs = count_references_by_type(refs)

    render_report_and_end(
        verbose,
        mode,
        extractor,
        url_count,
        citation_count,
        total_refs,
        total_latency,
        manifest,
    )

    # Write to disk
    write_manifest(manifest, out_dir)

    return manifest
