from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from core.reliability.retry import is_permanent_error, is_transient_error, retry_call
from ..types import GraphConfig, NodeResult


def _extract_once(
    text: str,
    resolved_cfg: Dict[str, Any],
) -> Tuple[list[Dict[str, Any]], Dict[str, int] | None, int | None, Dict[str, str]]:
    from core.infrastructure.extraction.langchain_agent import (
        LangChainExtractionAgent,
    )

    agent = LangChainExtractionAgent(cfg_override=resolved_cfg)
    data = agent.extract(text)
    extractions = list(data.get("references", [])) if isinstance(data, dict) else []
    tokens = getattr(agent, "last_tokens", None)
    latency_ms = getattr(agent, "last_extract_latency_ms", None)
    llm_info = {
        "provider": getattr(agent, "last_provider", None) or "",
        "model": getattr(agent, "last_model", None) or "",
    }
    return extractions, tokens, latency_ms, llm_info


def _heuristic_extractions(text: str) -> list[Dict[str, Any]]:
    from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent

    refs = HeuristicExtractionAgent().extract(text).get("references", [])
    return list(refs)


def _try_llm_extractions(
    text: str,
    cfg: GraphConfig,
) -> Tuple[list[Dict[str, Any]], Dict[str, int] | None, int | None, bool, Dict[str, str] | None]:
    from core.infrastructure.config.resolver import resolve_engine_config

    resolved_cfg, _ = resolve_engine_config(cfg.engine_overrides or {})
    if cfg.timeout_s is not None:
        resolved_cfg["timeout_s"] = cfg.timeout_s
    if cfg.retries is not None:
        resolved_cfg["retries"] = cfg.retries

    attempts = (cfg.retries or 0) + 1
    last_exc: Exception | None = None

    def _should_retry(e: Exception) -> bool:
        if is_permanent_error(e):
            return False
        return isinstance(e, TimeoutError) or is_transient_error(e)

    try:
        extractions, tokens, latency_ms, llm_info = retry_call(
            lambda: _extract_once(text, resolved_cfg),
            attempts,
            cfg.backoff_base_s,
            cfg.jitter_s,
            cfg.backoff_max_s,
            _should_retry,
        )
        return extractions, tokens, latency_ms, False, llm_info
    except Exception as e:  # noqa: BLE001
        last_exc = e
        if isinstance(last_exc, TimeoutError):
            if getattr(cfg, "use_fallback", True):
                return _heuristic_extractions(text), None, None, True, None
            raise last_exc
        if getattr(cfg, "use_fallback", True):
            return _heuristic_extractions(text), None, None, True, None
        return [], None, None, False, None


def _build_metrics(
    start: float,
    latency_ms: int | None,
    tokens: Dict[str, int] | None,
) -> Dict[str, Any]:
    lm = latency_ms if latency_ms is not None else int((time.time() - start) * 1000)
    return {"latency_ms": lm, "tokens": tokens or {"prompt": 0, "completion": 0}, "node": "extract"}


def run(text: str, _classifications: NodeResult, cfg: GraphConfig | None = None) -> NodeResult:
    start = time.time()
    if cfg and getattr(cfg, "enabled", False):
        extractions, tokens, latency_ms, _, llm_info = _try_llm_extractions(text, cfg)
    else:
        extractions, tokens, latency_ms = _heuristic_extractions(text), None, None
        llm_info = None
    metrics = _build_metrics(start, latency_ms, tokens)
    out: NodeResult = {"extractions": extractions, "metrics": metrics}
    if llm_info:
        out["llm"] = llm_info
    return out
