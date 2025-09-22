from __future__ import annotations

import pytest

from core.application.pipeline import build_manifest_from_text


def test_pipeline_integration_multitype_valid(monkeypatch, tmp_path):
    """Pipeline deve aceitar múltiplos tipos quando os details estão coerentes."""

    class DummyAgent:
        def extract(self, text: str):
            return {
                "references": [
                    {
                        "id": 1,
                        "rawString": "https://example.com",
                        "referenceType": "web_link",
                        "sourceFormat": "web_content",
                        "sourcePath": "https://example.com",
                        "details": {"title": "Homepage"},
                    },
                    {
                        "id": 2,
                        "rawString": "Doe (2020)",
                        "referenceType": "in_text_citation",
                        "sourceFormat": "text",
                        "sourcePath": "",
                        "details": {"author": "Doe", "year": 2020},
                    },
                ]
            }

    monkeypatch.setattr(
        "core.application.pipeline.HeuristicExtractionAgent", lambda: DummyAgent()
    )

    m = build_manifest_from_text("See Doe (2020) https://example.com", str(tmp_path))
    refs = m["knowledgeIndex"]["references"]
    assert len(refs) == 2
    assert {r["referenceType"] for r in refs} == {"web_link", "in_text_citation"}


def test_pipeline_integration_invalid_details_fails(monkeypatch, tmp_path):
    """Pipeline deve falhar quando details contém campos proibidos pelo schema do tipo."""

    class BadAgent:
        def extract(self, text: str):
            # referenceType in_text_citation não permite campo arbitrário foo em details
            return {
                "references": [
                    {
                        "id": 1,
                        "rawString": "Doe (2020)",
                        "referenceType": "in_text_citation",
                        "sourceFormat": "text",
                        "sourcePath": "",
                        "details": {"author": "Doe", "year": 2020, "foo": "bar"},
                    }
                ]
            }

    monkeypatch.setattr(
        "core.application.pipeline.HeuristicExtractionAgent", lambda: BadAgent()
    )

    with pytest.raises(ValueError) as ei:
        build_manifest_from_text("Doe (2020)", str(tmp_path))

    msg = str(ei.value)
    # Mensagem deve conter prefixo padrão e a localização do erro
    assert msg.startswith("Manifest validation failed:")
    assert "knowledgeIndex/references/0/details" in msg
    assert "Additional properties are not allowed" in msg
