from __future__ import annotations

from pathlib import Path

from core.application.pipeline import build_manifest_from_file


def test_build_manifest_from_file_txt(tmp_path: Path):
    p = tmp_path / "doc.txt"
    p.write_text("Hello https://example.org", encoding="utf-8")
    manifest = build_manifest_from_file(str(p), str(tmp_path))
    assert manifest["sourceDocument"]["sourceType"] == "file"
    assert manifest["knowledgeIndex"]["references"]
