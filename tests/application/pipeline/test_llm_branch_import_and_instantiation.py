from __future__ import annotations

import json
import sys
import types

from core.application.pipeline import build_manifest_from_text


class _FakeAgent:
    def __init__(self, cfg_override=None):
        self.cfg_override = cfg_override
        self.last_provider = None
        self.last_model = None
        self.last_tokens = None
        self.last_extract_latency_ms = None

    def extract(self, text: str):
        return {"references": []}


def test_llm_branch_uses_local_import_and_instantiation(tmp_path, monkeypatch):
    fake_mod = types.ModuleType("core.infrastructure.extraction.langchain_agent")
    fake_mod.LangChainExtractionAgent = _FakeAgent

    monkeypatch.setitem(
        sys.modules,
        "core.infrastructure.extraction.langchain_agent",
        fake_mod,
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    manifest = build_manifest_from_text(
        "content",
        str(out_dir),
        verbose=False,
        engine="llm",
        engine_overrides={"provider": "openai"},
    )
    assert manifest["sourceDocument"]["sourceType"] == "text"
    mf_path = out_dir / "manifest" / "manifest.json"
    assert mf_path.exists()
    data = json.loads(mf_path.read_text())
    assert data["manifestId"] == manifest["manifestId"]
