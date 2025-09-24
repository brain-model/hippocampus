from __future__ import annotations

import json

from core.application.pipeline import build_manifest_from_file


def test_file_verbose_branch_executes_and_writes(tmp_path, monkeypatch):
    # Capture prints
    printed = []

    def fake_line(s: str) -> None:
        printed.append(s)

    monkeypatch.setattr("core.application.pipeline.line", fake_line)

    # Criar arquivo de entrada simples
    src = tmp_path / "in.txt"
    src.write_text("Alpha http://example.com Beta")

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    manifest = build_manifest_from_file(
        str(src), str(out_dir), verbose=True, engine="heuristic"
    )
    assert manifest["sourceDocument"]["sourceType"] == "file"
    mf_path = out_dir / "manifest" / "manifest.json"
    assert mf_path.exists()
    data = json.loads(mf_path.read_text())
    assert data["manifestId"] == manifest["manifestId"]

    # Verifica que o summary foi impresso
    assert any("total_refs" in s or "Total refs" in s for s in printed)
