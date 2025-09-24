from __future__ import annotations

from typing import Any

from .nodes import classify as node_classify
from .nodes import consolidate as node_consolidate
from .nodes import extract as node_extract
from .types import GraphConfig, NodeResult


class GraphOrchestrator:
    def __init__(self, cfg: GraphConfig | None = None) -> None:
        self.cfg = cfg or GraphConfig()

    def run(self, text: str) -> dict[str, Any]:
        # Minimal stub flow: classify -> extract -> consolidate
        cls = self._node_classify(text)
        ext = self._node_extract(text, cls)
        out = self._node_consolidate(cls, ext)

        def _m(n: NodeResult) -> dict[str, Any]:
            return n.get("metrics", {}) if isinstance(n, dict) else {}

        def _tok(n: dict[str, Any]) -> dict[str, int]:
            t = n.get("tokens") if isinstance(n, dict) else None
            return t or {"prompt": 0, "completion": 0}

        m_cls = _m(cls)
        m_ext = _m(ext)
        m_con = _m(out)
        total_latency = (
            int(m_cls.get("latency_ms", 0))
            + int(m_ext.get("latency_ms", 0))
            + int(m_con.get("latency_ms", 0))
        )
        tk_cls = _tok(m_cls)
        tk_ext = _tok(m_ext)
        tk_con = _tok(m_con)
        total_tokens = {
            "prompt": (
                int(tk_cls.get("prompt", 0))
                + int(tk_ext.get("prompt", 0))
                + int(tk_con.get("prompt", 0))
            ),
            "completion": (
                int(tk_cls.get("completion", 0))
                + int(tk_ext.get("completion", 0))
                + int(tk_con.get("completion", 0))
            ),
        }
        out["metrics"] = {
            "total_latency_ms": total_latency,
            "total_tokens": total_tokens,
            "nodes": {
                "classify": m_cls,
                "extract": m_ext,
                "consolidate": m_con,
            },
        }
        # Bubble up LLM info if present on extract node
        if isinstance(ext, dict) and isinstance(ext.get("llm"), dict):
            out["llm"] = {
                "provider": ext["llm"].get("provider", ""),
                "model": ext["llm"].get("model", ""),
            }
        return out

    def _node_classify(self, _text: str) -> NodeResult:
        return node_classify.run(_text)

    def _node_extract(self, _text: str, _prev: NodeResult) -> NodeResult:
        return node_extract.run(_text, _prev, self.cfg)

    def _node_consolidate(self, _cls: NodeResult, ext: NodeResult) -> dict[str, Any]:
        return node_consolidate.run(_cls, ext)
