from __future__ import annotations

from core.noesis.graph.agent import GraphOrchestrator
from core.noesis.graph.types import GraphConfig


def test_graph_orchestrator_defaults_and_empty_flow():
    orch = GraphOrchestrator()
    out = orch.run("no urls here")
    assert isinstance(out, dict)
    assert out.get("references") == []
    # métricas agregadas presentes
    m = out.get("metrics")
    assert isinstance(m, dict)
    assert "total_latency_ms" in m
    assert "total_tokens" in m and set(m["total_tokens"]) >= {"prompt", "completion"}
    assert "nodes" in m and set(m["nodes"]) >= {"classify", "extract", "consolidate"}


def test_graph_orchestrator_cfg_is_stored():
    cfg = GraphConfig(enabled=True, use_fallback=True, timeout_s=5, retries=1)
    orch = GraphOrchestrator(cfg)
    assert orch.cfg.enabled is True
    assert orch.cfg.retries == 1


def test_graph_orchestrator_with_monkeypatched_extract(monkeypatch):
    orch = GraphOrchestrator()

    def fake_extract(_text: str, _prev):
        return {
            "extractions": [{"id": "r1"}],
            "metrics": {"latency_ms": 12, "tokens": {"prompt": 1, "completion": 2}},
        }

    monkeypatch.setattr(orch, "_node_extract", fake_extract)
    out = orch.run("see http://x")
    assert out.get("references") == [{"id": "r1"}]
    m = out.get("metrics")
    assert m["total_tokens"]["prompt"] >= 1
    assert m["total_latency_ms"] >= 12
