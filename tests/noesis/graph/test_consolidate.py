from __future__ import annotations

from core.noesis.graph.nodes import consolidate as node_consolidate


def test_consolidate_maps_extractions_to_references():
    extractions = {"extractions": [{"id": "r1"}, {"id": "r2"}]}
    out = node_consolidate.run({"classifications": []}, extractions)
    assert isinstance(out, dict)
    assert out.get("references") == extractions["extractions"]
    m = out.get("metrics")
    assert isinstance(m, dict)
    assert m.get("node") == "consolidate"
    assert isinstance(m.get("latency_ms"), int)
    assert m.get("tokens") == {"prompt": 0, "completion": 0}


def test_consolidate_handles_non_dict_input():
    out = node_consolidate.run(None, None)
    assert out.get("references") == []
    m = out.get("metrics")
    assert isinstance(m, dict)
    assert m.get("node") == "consolidate"
    assert isinstance(m.get("latency_ms"), int)
    assert m.get("tokens") == {"prompt": 0, "completion": 0}
