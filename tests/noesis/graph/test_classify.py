from __future__ import annotations

from core.noesis.graph.nodes import classify as node_classify


def test_classify_empty_text_returns_no_classifications_and_metrics():
    out = node_classify.run("")
    assert isinstance(out, dict)
    assert out.get("classifications") == []
    m = out.get("metrics")
    assert isinstance(m, dict)
    assert m.get("node") == "classify"
    assert isinstance(m.get("latency_ms"), int) and m["latency_ms"] >= 0
    tokens = m.get("tokens")
    assert isinstance(tokens, dict)
    assert set(tokens.keys()) >= {"prompt", "completion"}


def test_classify_single_url_detected():
    text = "Visit http://example.com for more info"
    out = node_classify.run(text)
    cl = out.get("classifications")
    assert isinstance(cl, list) and len(cl) == 1
    c0 = cl[0]
    assert c0.get("kind") == "web_link"
    assert c0.get("span") == "http://example.com"
    assert 0 <= c0.get("confidence", 0) <= 1


def test_classify_multiple_urls_and_order():
    text = "a http://a.com b https://b.org/page c"
    out = node_classify.run(text)
    spans = [c.get("span") for c in out.get("classifications", [])]
    assert spans == ["http://a.com", "https://b.org/page"]
