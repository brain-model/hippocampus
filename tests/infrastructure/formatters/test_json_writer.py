from __future__ import annotations

from pathlib import Path

from core.infrastructure.formatters.json_writer import ManifestJsonWriter


def test_writer_creates_manifest_file(tmp_out_dir: str):
    writer = ManifestJsonWriter()
    target = writer.write({"status": "Awaiting Consolidation"}, tmp_out_dir)
    p = Path(target)
    assert p.exists() and p.name == "manifest.json"
    data = p.read_text(encoding="utf-8")
    assert "manifestId" in data and "processedAt" in data and "status" in data
