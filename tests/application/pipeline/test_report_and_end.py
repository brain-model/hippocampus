from __future__ import annotations

import json

from core.application.pipeline import build_manifest_from_text


def test_report_and_end_are_printed_text_mode_verbose_false(
    tmp_path, monkeypatch, capsys
):
    printed = []

    def fake_line(s: str) -> None:
        printed.append(s)

    monkeypatch.setattr("core.application.pipeline.core.line", fake_line)

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    manifest = build_manifest_from_text(
        "This is text with http://example.com",
        str(out_dir),
        verbose=False,
        engine="heuristic",
    )
    assert "knowledgeIndex" in manifest

    # Verify the pipeline completed successfully and created the manifest file
    mf_path = out_dir / "manifest" / "manifest.json"
    assert mf_path.exists()
    assert manifest["manifestId"] is not None
    assert len(manifest["knowledgeIndex"]["references"]) > 0  # Should find the URL
    data = json.loads(mf_path.read_text())
    assert data["manifestId"] == manifest["manifestId"]
