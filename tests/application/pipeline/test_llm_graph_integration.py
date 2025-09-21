import json
from pathlib import Path

import pytest

from core.application.pipeline import (
    build_manifest_from_file,
    build_manifest_from_text,
)


@pytest.fixture()
def fake_graph_run(monkeypatch):
    class FakeGraph:
        def __init__(self, cfg):
            self.cfg = cfg

        def run(self, text: str):
            return {
                "references": [
                    {
                        "id": 1,
                        "rawString": "https://example.com",
                        "referenceType": "web_link",
                        "sourceFormat": "web_content",
                        "sourcePath": "https://example.com",
                        "details": {},
                    }
                ],
                "metrics": {"total_tokens": {"prompt": 1, "completion": 2}},
            }

    def _fake_ctor(cfg):
        return FakeGraph(cfg)

    monkeypatch.setattr(
        "core.noesis.graph.agent.GraphOrchestrator", _fake_ctor, raising=True
    )


def test_build_manifest_from_text_llm_graph(tmp_path, fake_graph_run):
    out_dir = tmp_path / "out"
    m = build_manifest_from_text(
        text="Visit https://example.com/",
        out_dir=str(out_dir),
        verbose=False,
        engine="llm-graph",
    )
    assert m["knowledgeIndex"]["references"] == [
        {
            "id": 1,
            "rawString": "https://example.com",
            "referenceType": "web_link",
            "sourceFormat": "web_content",
            "sourcePath": "https://example.com",
            "details": {},
        }
    ]
    # Verifica escrita do manifest em disco
    manifest_path = Path(out_dir) / "manifest" / "manifest.json"
    assert manifest_path.exists()

    saved = json.loads(manifest_path.read_text())
    assert saved["manifestId"] == m["manifestId"]


def test_build_manifest_from_file_llm_graph(tmp_path, fake_graph_run):
    # Cria arquivo de texto simples
    src = tmp_path / "input.txt"
    src.write_text("A link: https://example.com/")

    out_dir = tmp_path / "out"
    m = build_manifest_from_file(
        file_path=str(src),
        out_dir=str(out_dir),
        verbose=True,
        engine="llm-graph",
    )
    assert m["knowledgeIndex"]["references"][0]["sourcePath"] == "https://example.com"
    # Verifica escrita do manifest
    manifest_path = Path(out_dir) / "manifest" / "manifest.json"
    assert manifest_path.exists()
