from __future__ import annotations

from pathlib import Path

from core.application.pipeline import build_manifest_from_file, build_manifest_from_text
from core.infrastructure.extraction.heuristic import HeuristicExtractionAgent


def test_pipeline_builds_and_writes(tmp_out_dir: str):
    text = "See https://example.com (Doe, 2020)."
    m = build_manifest_from_text(text, tmp_out_dir)
    # Checa campos principais
    assert m["manifestVersion"] == "1.0.0"
    assert m["status"] == "Awaiting Consolidation"
    # Arquivo foi escrito no disco
    p = Path(tmp_out_dir) / "manifest" / "manifest.json"
    assert p.exists()


def test_pipeline_basic_text_input(tmp_out_dir: str):
    """Testa processamento básico de texto."""
    text = "This is a simple test."
    m = build_manifest_from_text(text, tmp_out_dir)
    assert m["manifestVersion"] == "1.0.0"
    assert m["status"] == "Awaiting Consolidation"


def test_pipeline_basic_file_input(tmp_path):
    """Testa processamento básico de arquivo."""
    f = tmp_path / "input.txt"
    f.write_text("Test content from file", encoding="utf-8")
    m = build_manifest_from_file(str(f), str(tmp_path))
    assert m["manifestVersion"] == "1.0.0"
    assert m["status"] == "Awaiting Consolidation"


# === TESTES AVANÇADOS DE FUNCIONALIDADES CORE ===


def test_file_pipeline_detailed_logging(tmp_path, monkeypatch):
    """Testa logs detalhados no pipeline de arquivo"""
    monkeypatch.chdir(tmp_path)

    # Criar arquivo com extensão específica
    test_file = tmp_path / "document.md"
    test_file.write_text("# Test Document\nWith some content", encoding="utf-8")

    class DummyAgent:
        def extract(self, text):
            return {
                "references": [
                    {
                        "id": 1,
                        "referenceType": "web_link",
                        "rawString": "https://example.com",
                        "sourceFormat": "web_content",
                        "sourcePath": "https://example.com",
                        "details": {},
                    },
                    {
                        "id": 2,
                        "referenceType": "in_text_citation",
                        "rawString": "Smith (2023)",
                        "sourceFormat": "text",
                        "sourcePath": "",
                        "details": {},
                    },
                ]
            }

    monkeypatch.setattr(
        "core.application.pipeline.HeuristicExtractionAgent", lambda: DummyAgent()
    )

    result = build_manifest_from_file(
        str(test_file), str(tmp_path), engine="heuristic", verbose=False
    )

    # Verificar que o pipeline executou com sucesso
    assert result["status"] == "Awaiting Consolidation"
    assert len(result["knowledgeIndex"]["references"]) == 2


def test_manifest_id_and_timestamp_generation(tmp_path, monkeypatch):
    """Testa geração de ID único e timestamp do manifesto"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        HeuristicExtractionAgent, "extract", lambda self, text: {"references": []}
    )

    # Executar duas vezes para verificar IDs únicos
    result1 = build_manifest_from_text("Test1", str(tmp_path))
    result2 = build_manifest_from_text("Test2", str(tmp_path))

    # IDs devem ser únicos
    assert result1["manifestId"] != result2["manifestId"]
    assert len(result1["manifestId"]) == 32  # UUID hex

    # Timestamps devem estar presentes e válidos
    assert "processedAt" in result1
    assert "processedAt" in result2
    from datetime import datetime

    # Verificar formato ISO
    datetime.fromisoformat(result1["processedAt"].replace("Z", "+00:00"))


def test_file_format_detection_edge_cases(tmp_path, monkeypatch):
    """Testa detecção de formato para arquivos sem extensão"""
    from unittest.mock import patch

    monkeypatch.chdir(tmp_path)

    # Criar arquivo sem extensão
    test_file = tmp_path / "README"
    test_file.write_text("File without extension", encoding="utf-8")

    class DummyAgent:
        def extract(self, text):
            return {"references": []}

    with patch("core.application.pipeline.line") as mock_line:
        monkeypatch.setattr(
            "core.infrastructure.extraction.heuristic.HeuristicExtractionAgent",
            lambda: DummyAgent(),
        )

        build_manifest_from_file(str(test_file), str(tmp_path))

        # Verificar que formato "file" foi usado como fallback
        log_calls = [str(call) for call in mock_line.call_args_list]
        assert any("format=file" in call for call in log_calls)
