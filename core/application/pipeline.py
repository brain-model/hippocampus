"""Application pipeline for building and validating manifests.

This module orchestrates the MVP pipeline:
- Normalizes input text via `TextLoader`.
- Extracts heuristic references via `HeuristicExtractionAgent`.
- Assembles a minimal manifest dictionary with metadata.
- Validates against the JSON Schema at `MANIFEST_SCHEMA_PATH`.
- Persists the result as JSON in `out_dir/manifest/manifest.json`.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from core.domain.manifest import MANIFEST_VERSION, STATUS_AWAITING
from core.infrastructure.config.resolver import resolve_engine_config
from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent
from core.infrastructure.formatters.json_writer import ManifestJsonWriter
from core.infrastructure.loaders.registry import get_loader_for_file
from core.infrastructure.loaders.text import TextLoader
from core.resources import MANIFEST_SCHEMA_PATH
from core.resources.templates import render_template
from core.ui.console import (collect_section, friendly_ts, line, progress_bar,
                             summary_panel)
from core.noesis.graph.types import GraphConfig

from .validation import validate_manifest

_TPL_BEGIN = "cli/begin_generic.j2"
_TPL_LOAD = "cli/phase_load_generic.j2"
_TPL_EXTRACT = "cli/phase_extract_generic.j2"
_TPL_SUMMARY = "cli/summary_generic.j2"
_TPL_END = "cli/end_generic.j2"
_TPL_REPORT = "cli/report_generic.j2"


def _render_report_and_end(
    verbose: bool,
    mode: str,
    extractor: Any,
    url_count: int,
    citation_count: int,
    refs_len: int,
    total_latency: int,
    manifest: Dict[str, Any],
):
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
            getattr(extractor, "last_graph_total_ms", None)
            if mode == "llm"
            else None
        ),
        graph_tokens=(
            getattr(extractor, "last_graph_tokens", None)
            if mode == "llm"
            else None
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


def _log_begin(
    mode: str,
    source_type: str,
    source_format: str,
    resolved_cfg: Dict[str, Any],
    provenance: Dict[str, str],
) -> None:
    line(f"begin={mode} | source={source_type} | format={source_format}")
    if mode == "llm" and resolved_cfg:
        prov = ", ".join(
            f"{k}({provenance.get(k)})={v}" for k, v in resolved_cfg.items()
        )
        line(f"engine: {prov}")


def _extract_with_timing(
    extractor: Any, normalized: str, mode: str
) -> tuple[dict, int]:
    start = time.time()
    extracted = extractor.extract(normalized)
    latency = int((time.time() - start) * 1000)
    if mode == "llm" and getattr(extractor, "last_extract_latency_ms", None) is None:
        try:
            setattr(extractor, "last_extract_latency_ms", latency)
        except Exception:
            pass
    return extracted, latency


class GraphExtractorAdapter:
    def __init__(self, cfg: Any) -> None:
        self.cfg = cfg
        self.last_provider = None
        self.last_model = None
        self.last_tokens = None  # tokens from LLM extraction step, when available
        self.last_extract_latency_ms = None
        self.last_graph_total_ms = None
        self.last_graph_tokens = None

    def extract(self, text: str) -> dict:
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


def build_manifest_from_text(
    text: str,
    out_dir: str,
    verbose: bool = False,
    engine: str = "heuristic",
    engine_overrides: Dict[str, Any] | None = None,
    graph_config: Any | None = None,
) -> Dict[str, Any]:
    """Build and persist a manifest from input text.

    The flow loads and normalizes the text, extracts references, assembles
    the manifest dictionary, validates it against the JSON Schema, and writes
    the resulting JSON file to disk.

    Args:
        text: Input content to be indexed and analyzed.
        out_dir: Base directory where the JSON will be saved (subfolder `manifest`).

    Returns:
        The validated manifest dictionary persisted on disk.

    Raises:
        ValueError: If schema validation fails.
        OSError: If directory creation or file writing fails.
    """
    loader = TextLoader()
    use_graph = engine == "llm-graph"
    if engine in {"heuristic", "llm", "llm-graph"}:
        mode = "llm" if use_graph else engine
    else:
        mode = "heuristic"
    if mode == "llm":
        resolved_cfg, provenance = resolve_engine_config(engine_overrides or {})
    else:
        resolved_cfg, provenance = {}, {}
    if mode == "llm":
        from core.infrastructure.extraction.langchain_agent import \
            LangChainExtractionAgent

        if use_graph:
            # Merge CLI graph_config with resolved LLM cfg as engine_overrides
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
            extractor = GraphExtractorAdapter(cfg)
        else:
            extractor = LangChainExtractionAgent(cfg_override=resolved_cfg)
    else:
        extractor = HeuristicExtractionAgent()
    writer = ManifestJsonWriter()

    if not verbose:
        with collect_section("Collect"):
            # início + UI normal
            line(
                render_template(
                    _TPL_BEGIN,
                    mode=mode,
                    source_type="text",
                    source_format="text",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            t0 = time.time()
            with progress_bar(["load", "extract"]) as (prog, tasks):
                normalized = loader.load(text=text)
                prog.update(tasks["load"], advance=1)
                extracted = extractor.extract(normalized)
                prog.update(tasks["extract"], advance=1)
            total_latency = int((time.time() - t0) * 1000)

            refs = extracted.get("references", [])
            url_count = sum(1 for r in refs if r.get("referenceType") == "web_link")
            citation_count = sum(
                1 for r in refs if r.get("referenceType") == "in_text_citation"
            )
            line(
                render_template(
                    _TPL_SUMMARY,
                    mode=mode,
                    url_count=url_count,
                    citation_count=citation_count,
                    total_refs=len(refs),
                    latency_ms=total_latency,
                )
            )
    else:
        # stream de logs simples (sem UI de banners durante a execução)
        t0 = time.time()
        _log_begin(mode, "text", "text", resolved_cfg, provenance)
        load_start = time.time()
        normalized = loader.load(text=text)
        load_latency = int((time.time() - load_start) * 1000)
        line(
            render_template(
                _TPL_LOAD,
                mode=mode,
                loader_name=type(loader).__name__,
                latency_ms=load_latency,
                char_count=len(normalized or ""),
            )
        )
        extracted, extract_latency = _extract_with_timing(extractor, normalized, mode)
        line(
            render_template(
                _TPL_EXTRACT,
                mode=mode,
                url_count=sum(
                    1
                    for r in extracted.get("references", [])
                    if r.get("referenceType") == "web_link"
                ),
                citation_count=sum(
                    1
                    for r in extracted.get("references", [])
                    if r.get("referenceType") == "in_text_citation"
                ),
                total_refs=len(extracted.get("references", [])),
                latency_ms=extract_latency,
            )
        )
        total_latency = int((time.time() - t0) * 1000)
        refs = extracted.get("references", [])
        url_count = sum(1 for r in refs if r.get("referenceType") == "web_link")
        citation_count = sum(
            1 for r in refs if r.get("referenceType") == "in_text_citation"
        )
        line(
            render_template(
                _TPL_SUMMARY,
                mode=mode,
                url_count=url_count,
                citation_count=citation_count,
                total_refs=len(refs),
                latency_ms=total_latency,
            )
        )

    manifest: Dict[str, Any] = {
        "manifestVersion": MANIFEST_VERSION,
        "status": STATUS_AWAITING,
        "sourceDocument": {
            "sourceType": "text",
            "source": normalized[:5000],
            "sourceFormat": "text",
        },
        "knowledgeIndex": {
            "references": extracted.get("references", []),
        },
    }

    manifest["manifestId"] = uuid4().hex
    manifest["processedAt"] = datetime.now(timezone.utc).isoformat()

    validate_manifest(manifest, MANIFEST_SCHEMA_PATH)
    _render_report_and_end(
        verbose,
        mode,
        extractor,
        url_count,
        citation_count,
        len(refs),
        total_latency,
        manifest,
    )
    writer.write(manifest, out_dir)
    return manifest


def build_manifest_from_file(
    file_path: str,
    out_dir: str,
    verbose: bool = False,
    engine: str = "heuristic",
    engine_overrides: Dict[str, Any] | None = None,
    graph_config: Any | None = None,
) -> Dict[str, Any]:
    """Build and persist a manifest from an input file.

    Selects an appropriate loader based on the file extension, normalizes
    the content, extracts references, assembles the manifest, validates it
    and writes the resulting JSON file to disk.

    Args:
        file_path: Path to the input file.
        out_dir: Base directory where the JSON will be saved.

    Returns:
        The validated manifest dictionary persisted on disk.

    Raises:
        ValueError: If schema validation fails.
        OSError: If file reading or writing fails.
    """
    loader = get_loader_for_file(file_path)
    use_graph = engine == "llm-graph"
    if engine in {"heuristic", "llm", "llm-graph"}:
        mode = "llm" if use_graph else engine
    else:
        mode = "heuristic"
    if mode == "llm":
        resolved_cfg, provenance = resolve_engine_config(engine_overrides or {})
    else:
        resolved_cfg, provenance = {}, {}
    if mode == "llm":
        from core.infrastructure.extraction.langchain_agent import \
            LangChainExtractionAgent

        if use_graph:
            cfg = GraphConfig(enabled=True)
            if graph_config:
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
            extractor = GraphExtractorAdapter(cfg)
        else:
            extractor = LangChainExtractionAgent(cfg_override=resolved_cfg)
    else:
        extractor = HeuristicExtractionAgent()
    writer = ManifestJsonWriter()

    if not verbose:
        with collect_section("Collect"):
            line(
                render_template(
                    _TPL_BEGIN,
                    mode=mode,
                    source_type="file",
                    source_format=Path(file_path).suffix.lstrip(".") or "file",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

            t0 = time.time()
            with progress_bar(["load", "extract"]) as (prog, tasks):
                normalized = loader.load(file_path=file_path)
                prog.update(tasks["load"], advance=1)
                extracted = extractor.extract(normalized)
                prog.update(tasks["extract"], advance=1)
            total_latency = int((time.time() - t0) * 1000)

            refs = extracted.get("references", [])
            url_count = sum(1 for r in refs if r.get("referenceType") == "web_link")
            citation_count = sum(
                1 for r in refs if r.get("referenceType") == "in_text_citation"
            )

            line(
                render_template(
                    _TPL_SUMMARY,
                    mode=mode,
                    url_count=url_count,
                    citation_count=citation_count,
                    total_refs=len(refs),
                    latency_ms=total_latency,
                )
            )
    else:
        t0 = time.time()
        fmt = Path(file_path).suffix.lstrip(".") or "file"
        _log_begin(mode, "file", fmt, resolved_cfg, provenance)
        load_start = time.time()
        normalized = loader.load(file_path=file_path)
        load_latency = int((time.time() - load_start) * 1000)
        line(
            render_template(
                _TPL_LOAD,
                mode=mode,
                loader_name=type(loader).__name__,
                latency_ms=load_latency,
                char_count=len(normalized or ""),
            )
        )
        extracted, extract_latency = _extract_with_timing(extractor, normalized, mode)
        line(
            render_template(
                _TPL_EXTRACT,
                mode=mode,
                url_count=sum(
                    1
                    for r in extracted.get("references", [])
                    if r.get("referenceType") == "web_link"
                ),
                citation_count=sum(
                    1
                    for r in extracted.get("references", [])
                    if r.get("referenceType") == "in_text_citation"
                ),
                total_refs=len(extracted.get("references", [])),
                latency_ms=extract_latency,
            )
        )
        total_latency = int((time.time() - t0) * 1000)
        refs = extracted.get("references", [])
        url_count = sum(1 for r in refs if r.get("referenceType") == "web_link")
        citation_count = sum(
            1 for r in refs if r.get("referenceType") == "in_text_citation"
        )
        line(
            render_template(
                _TPL_SUMMARY,
                mode=mode,
                url_count=url_count,
                citation_count=citation_count,
                total_refs=len(refs),
                latency_ms=total_latency,
            )
        )

    manifest: Dict[str, Any] = {
        "manifestVersion": MANIFEST_VERSION,
        "status": STATUS_AWAITING,
        "sourceDocument": {
            "sourceType": "file",
            "source": normalized[:5000],
            "sourceFormat": Path(file_path).suffix.lstrip(".") or "file",
        },
        "knowledgeIndex": {
            "references": extracted.get("references", []),
        },
    }

    manifest["manifestId"] = uuid4().hex
    manifest["processedAt"] = datetime.now(timezone.utc).isoformat()

    validate_manifest(manifest, MANIFEST_SCHEMA_PATH)
    _render_report_and_end(
        verbose,
        mode,
        extractor,
        url_count,
        citation_count,
        len(refs),
        total_latency,
        manifest,
    )
    writer.write(manifest, out_dir)
    return manifest
