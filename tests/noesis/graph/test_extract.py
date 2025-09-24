from __future__ import annotations

from core.noesis.graph.nodes import extract as node_extract
from core.noesis.graph.types import GraphConfig


def test_extract_stub_returns_empty_extractions_and_metrics_dict():
    prev = {
        "classifications": [{"kind": "web_link", "confidence": 0.9, "span": "http://x"}]
    }
    out = node_extract.run("some text", prev, GraphConfig(enabled=False))
    assert isinstance(out, dict)
    assert out.get("extractions") == []
    m = out.get("metrics")
    assert isinstance(m, dict)
    assert m.get("node") == "extract"
    assert isinstance(m.get("latency_ms"), int)
    assert isinstance(m.get("tokens"), dict)


def test_extract_accepts_previous_node_result():
    prev = {"classifications": []}
    out = node_extract.run("anything", prev, GraphConfig(enabled=False))
    assert "extractions" in out
    assert "metrics" in out
