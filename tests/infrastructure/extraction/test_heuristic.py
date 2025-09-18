from __future__ import annotations

from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent


def test_extract_url_and_citation():
    text = "See https://example.com Doe (2020)."
    agent = HeuristicExtractionAgent()
    out = agent.extract(text)
    refs = out["references"]
    assert any(r["referenceType"] == "web_link" for r in refs)
    assert any(r["referenceType"] == "in_text_citation" for r in refs)


def test_extract_empty_text():
    agent = HeuristicExtractionAgent()
    out = agent.extract("")
    assert out == {"references": []}
