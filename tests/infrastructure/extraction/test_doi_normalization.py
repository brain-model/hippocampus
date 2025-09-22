from __future__ import annotations

from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


def test_doi_normalization_strips_and_collapses_whitespace():
    agent = LangChainExtractionAgent(cfg_override={})

    data = {
        "references": [
            {"title": "A", "doi": " 10.1000 / 182 "},
            {"title": "B", "doi": "10.1000/xyz\n 123 \t 45"},
        ]
    }
    out = agent._normalize_output(data)
    refs = out["references"]

    # Primeiro item: DOI deve ficar sem espaços e URL montada
    r1 = refs[0]
    assert r1["sourcePath"] == "https://doi.org/10.1000/182"
    assert r1["details"]["doi"] == "10.1000/182"

    # Segundo item: DOI com quebras e tabs deve ser colapsado
    r2 = refs[1]
    assert r2["sourcePath"] == "https://doi.org/10.1000/xyz12345"
    assert r2["details"]["doi"] == "10.1000/xyz12345"


def test_doi_preserve_url_if_provided():
    agent = LangChainExtractionAgent(cfg_override={})

    data = {
        "references": [
            {"title": "A", "doi": "10.1000/182", "url": "https://example.com/paper"},
        ]
    }
    out = agent._normalize_output(data)
    refs = out["references"]

    r = refs[0]
    # Se URL já vier, mantemos a URL original
    assert r["sourcePath"] == "https://example.com/paper"
    # Mas o DOI ainda é normalizado no details
    assert r["details"]["doi"] == "10.1000/182"
