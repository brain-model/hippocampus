from __future__ import annotations

from pathlib import Path

from core.cli.root import main


def test_collect_invalid_reference_schema_error_template_output(
    tmp_path: Path, monkeypatch, capsys
):
    """CLI collect deve retornar 1 e imprimir erro padronizado
    quando schema falhar.
    """

    class BadAgent:
        def extract(self, text: str):
            # referenceType web_link com details contendo propriedade inesperada
            # quebra schema
            return {
                "references": [
                    {
                        "id": 1,
                        "rawString": "See https://example.com",
                        "referenceType": "web_link",
                        "details": {"foo": "bar"},
                    }
                ]
            }

    monkeypatch.setattr(
        "core.application.pipeline.HeuristicExtractionAgent", lambda: BadAgent()
    )

    out_dir = tmp_path / "out"
    code = main(["collect", "-t", "dummy text", "-o", str(out_dir)])
    assert code == 1
    err = capsys.readouterr().err
    # Deve estar no formato do template com título contendo "Invalid value: ..."
    assert "Invalid value:" in err
    assert "Manifest validation failed:" in err


def test_collect_file_invalid_reference_schema_error_template_output(
    tmp_path: Path, monkeypatch, capsys
):
    """CLI collect (modo arquivo) deve retornar 1 e imprimir erro
    padronizado quando schema falhar.
    """

    class BadAgent:
        def extract(self, text: str):
            return {
                "references": [
                    {
                        "id": 1,
                        "rawString": "See https://example.com",
                        "referenceType": "web_link",
                        "details": {"foo": "bar"},
                    }
                ]
            }

    monkeypatch.setattr(
        "core.application.pipeline.HeuristicExtractionAgent", lambda: BadAgent()
    )

    src = tmp_path / "doc.txt"
    src.write_text("content", encoding="utf-8")
    out_dir = tmp_path / "outf"
    code = main(["collect", "-f", str(src), "-o", str(out_dir)])
    assert code == 1
    err = capsys.readouterr().err
    assert "Invalid value:" in err
    assert "Manifest validation failed:" in err


def test_collect_incompatible_manifest_version_error(
    tmp_path: Path, monkeypatch, capsys
):
    """CLI collect deve falhar com versões incompatíveis do manifesto (>=2.0.0)."""

    # Garante que a extração é válida para isolar o erro de versão
    class GoodAgent:
        def extract(self, text: str):
            return {"references": []}

    monkeypatch.setattr(
        "core.application.pipeline.HeuristicExtractionAgent", lambda: GoodAgent()
    )
    # Força versão incompatível no pipeline
    monkeypatch.setattr(
        "core.application.pipeline.MANIFEST_VERSION", "2.0.0", raising=False
    )

    out_dir = tmp_path / "out"
    code = main(["collect", "-t", "dummy", "-o", str(out_dir)])
    assert code == 1
    err = capsys.readouterr().err
    assert "Invalid value:" in err
    assert "manifestVersion: incompatible major" in err
