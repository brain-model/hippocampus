from __future__ import annotations

from pathlib import Path

from core.application.pipeline import build_manifest_from_text


def test_pipeline_builds_and_writes(tmp_out_dir: str):
    text = "See https://example.com (Doe, 2020)."
    m = build_manifest_from_text(text, tmp_out_dir)
    # Checa campos principais
    assert m["manifestVersion"] == "1.0.0"
    assert m["status"] == "Awaiting Consolidation"
    # Arquivo foi escrito no disco
    p = Path(tmp_out_dir) / "manifest" / "manifest.json"
    assert p.exists()
