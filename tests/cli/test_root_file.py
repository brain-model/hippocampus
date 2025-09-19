from __future__ import annotations

from pathlib import Path

from core.cli.root import main


def test_cli_file_success(tmp_path: Path, capsys):
    p = tmp_path / "doc.md"
    p.write_text("# T\nsee [x](https://ex.com)", encoding="utf-8")
    code = main(["--file", str(p), "-o", str(tmp_path)])
    assert code == 0
