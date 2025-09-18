from __future__ import annotations

from pathlib import Path

import pytest

from core.cli.root import main


def test_cli_help_runs():
    # argparse renderiza help e sai com 0 ao passar --help
    with pytest.raises(SystemExit) as ei:
        main(["--help"])  # type: ignore[arg-type]
    assert ei.value.code == 0


def test_cli_text_success(tmp_path: Path):
    out_dir = tmp_path / "out"
    code = main(["-t", "See https://example.com", "-o", str(out_dir)])
    assert code == 0
    assert (out_dir / "manifest" / "manifest.json").exists()


def test_cli_file_disabled(tmp_path: Path):
    # --file deve ser rejeitado no MVP
    with pytest.raises(SystemExit) as ei:
        main(["-f", "foo.txt"])  # type: ignore[arg-type]
    assert ei.value.code == 2  # argparse usage error


def test_cli_error_propagates_when_verbose(monkeypatch, tmp_path: Path):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("core.cli.root.build_manifest_from_text", boom)
    with pytest.raises(RuntimeError):
        main(["-t", "x", "-o", str(tmp_path), "--verbose"])  # type: ignore[arg-type]


def test_cli_error_stderr_when_not_verbose(monkeypatch, tmp_path: Path, capsys):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("core.cli.root.build_manifest_from_text", boom)
    code = main(["-t", "x", "-o", str(tmp_path)])
    assert code == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err
