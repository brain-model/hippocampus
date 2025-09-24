import pytest

from core.application import pipeline


def test_pipeline_manifest_validation_error(monkeypatch, tmp_path):
    # Simula erro de validação do manifesto
    def fake_validate_manifest(manifest, schema_path):
        raise RuntimeError("Manifesto inválido")

    monkeypatch.setattr(pipeline, "validate_manifest", fake_validate_manifest)
    with pytest.raises(RuntimeError, match="Manifesto inválido"):
        pipeline.build_manifest_from_text("Texto", str(tmp_path))


def test_pipeline_persist_error(monkeypatch, tmp_path):
    # Simula erro ao persistir arquivo
    class BadWriter:
        def write(self, manifest, out_dir):
            raise RuntimeError("Erro ao persistir arquivo")

    monkeypatch.setattr(pipeline, "ManifestJsonWriter", lambda: BadWriter())
    with pytest.raises(RuntimeError, match="Erro ao persistir arquivo"):
        pipeline.build_manifest_from_text("Texto", str(tmp_path))


def test_pipeline_agent_timeout(monkeypatch, tmp_path):
    # Simula timeout do agente
    class BadAgent:
        def extract(self, text):
            raise TimeoutError("timeout")

    monkeypatch.setattr(pipeline, "HeuristicExtractionAgent", lambda: BadAgent())
    with pytest.raises(TimeoutError):
        pipeline.build_manifest_from_text("Texto", str(tmp_path))


def test_pipeline_loader_error(monkeypatch, tmp_path):
    # Simula erro no loader
    class BadLoader:
        def load(self, text=None, file_path=None):
            raise RuntimeError("Erro no loader")

    monkeypatch.setattr(pipeline, "TextLoader", BadLoader)
    with pytest.raises(RuntimeError, match="Erro no loader"):
        pipeline.build_manifest_from_text("Texto", str(tmp_path))


def test_pipeline_agent_extraction_error(monkeypatch, tmp_path):
    # Simula erro na extração
    class BadAgent:
        def extract(self, text):
            raise ValueError("Erro na extração")

    monkeypatch.setattr(pipeline, "HeuristicExtractionAgent", lambda: BadAgent())
    with pytest.raises(ValueError, match="Erro na extração"):
        pipeline.build_manifest_from_text("Texto", str(tmp_path))


# === TESTES EDGE CASES E ERROR HANDLING ===


def test_extract_timing_fallback_latency(tmp_path, monkeypatch):
    """Testa fallback de latency quando extractor não tem last_extract_latency_ms"""
    monkeypatch.chdir(tmp_path)

    class DummyAgent:
        def __init__(self):
            # Não define last_extract_latency_ms para trigger do setattr
            pass

        def extract(self, text):
            # Simula demora para testar timing
            import time

            time.sleep(0.01)
            return {"references": []}

    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent",
        lambda **kwargs: DummyAgent(),
    )

    result = pipeline.build_manifest_from_text(
        "Test text", str(tmp_path), engine="llm", verbose=False
    )

    # Verificar que o pipeline executou com sucesso
    assert result["status"] == "Awaiting Consolidation"


def test_extract_timing_setattr_exception(tmp_path, monkeypatch):
    """Testa quando setattr falha ao definir latency"""
    monkeypatch.chdir(tmp_path)

    class ReadOnlyAgent:
        def extract(self, text):
            return {"references": []}

        def __setattr__(self, name, value):
            if name == "last_extract_latency_ms":
                raise AttributeError("Read-only attribute")
            super().__setattr__(name, value)

    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent",
        lambda **kwargs: ReadOnlyAgent(),
    )

    # Não deve lançar exceção mesmo com setattr falhando
    result = pipeline.build_manifest_from_text(
        "Test text", str(tmp_path), engine="llm", verbose=False
    )

    assert result["status"] == "Awaiting Consolidation"
