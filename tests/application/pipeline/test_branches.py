from core.application import pipeline


def test_pipeline_branch_invalid_engine(monkeypatch, tmp_path):
    # engine desconhecido deve cair no modo heurístico
    m = pipeline.build_manifest_from_text("Texto", str(tmp_path), engine="desconhecido")
    assert m["status"] == "Awaiting Consolidation"


def test_pipeline_branch_verbose(monkeypatch, tmp_path):
    # Testa branch verbose
    class DummyLoader:
        def load(self, text=None, file_path=None):
            return "conteúdo"

    class DummyAgent:
        def extract(self, text):
            return {"references": []}

    monkeypatch.setattr(pipeline, "TextLoader", DummyLoader)
    monkeypatch.setattr(pipeline, "HeuristicExtractionAgent", lambda: DummyAgent())
    m = pipeline.build_manifest_from_text("Texto", str(tmp_path), verbose=True)
    assert m["status"] == "Awaiting Consolidation"


def test_pipeline_branch_llm(monkeypatch, tmp_path):
    # Testa branch engine="llm" com overrides, mockando LangChainExtractionAgent
    class DummyAgent:
        def extract(self, text):
            return {
                "references": [
                    {
                        "id": 1,
                        "rawString": "ref",
                        "referenceType": "web_link",
                        "sourceFormat": "web_content",
                        "sourcePath": "ref",
                        "details": {},
                    }
                ]
            }

    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent",
        lambda **kwargs: DummyAgent(),
    )
    m = pipeline.build_manifest_from_text(
        "Texto",
        str(tmp_path),
        engine="llm",
        engine_overrides={"provider": "openai", "model": "gpt-4o-mini"},
    )
    assert m["status"] == "Awaiting Consolidation"
    assert "references" in m["knowledgeIndex"]
    assert m["knowledgeIndex"]["references"][0]["rawString"] == "ref"


def test_pipeline_branch_file(monkeypatch, tmp_path):
    # Testa branch de arquivo
    f = tmp_path / "input.txt"
    f.write_text("Ref: https://arxiv.org/abs/1234.5678", encoding="utf-8")

    class DummyLoader:
        def load(self, text=None, file_path=None):
            return "conteúdo"

    monkeypatch.setattr(pipeline, "TextLoader", DummyLoader)
    m = pipeline.build_manifest_from_file(str(f), str(tmp_path))
    assert m["status"] == "Awaiting Consolidation"


def test_pipeline_engine_overrides(monkeypatch, tmp_path):
    # Testa aplicação de overrides do engine
    class DummyAgent:
        def __init__(self, **kwargs):
            self.config = kwargs

        def extract(self, text):
            return {"references": []}

    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent",
        DummyAgent,
    )
    m = pipeline.build_manifest_from_text(
        "Texto",
        str(tmp_path),
        engine="llm",
        engine_overrides={"temperature": 0.5, "model": "gpt-3.5-turbo"},
    )
    assert m["status"] == "Awaiting Consolidation"


def test_pipeline_agent_selection_heuristic(monkeypatch, tmp_path):
    # Testa seleção do agente heurístico
    class DummyAgent:
        def extract(self, text):
            return {"references": []}

    monkeypatch.setattr(pipeline, "HeuristicExtractionAgent", lambda: DummyAgent())
    m = pipeline.build_manifest_from_text("Texto", str(tmp_path), engine="heuristic")
    assert m["status"] == "Awaiting Consolidation"


# === TESTES VERBOSE E LLM LOGGING ===


def test_verbose_log_begin_with_llm_provenance(tmp_path, monkeypatch):
    """Testa _log_begin com logs verbose e provenance do LLM"""
    from unittest.mock import patch

    monkeypatch.chdir(tmp_path)

    class DummyAgent:
        def extract(self, text):
            return {"references": []}

    # Mock para capturar logs verbose
    with patch("core.application.pipeline.line") as mock_line:
        monkeypatch.setattr(
            "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent",
            lambda **kwargs: DummyAgent(),
        )

        pipeline.build_manifest_from_text(
            "Test text",
            str(tmp_path),
            engine="llm",
            engine_overrides={"provider": "openai", "model": "gpt-4"},
            verbose=True,
        )

        # Verificar se logs de provenance foram chamados
        log_calls = [str(call) for call in mock_line.call_args_list]
        assert any("begin=llm" in call for call in log_calls)
        assert any("engine:" in call for call in log_calls)


def test_non_verbose_llm_provenance_logging(tmp_path, monkeypatch):
    """Testa logs de provenance no modo não-verbose"""
    from unittest.mock import patch

    monkeypatch.chdir(tmp_path)

    class DummyAgent:
        def extract(self, text):
            return {"references": []}

    with patch("core.application.pipeline.line") as mock_line:
        monkeypatch.setattr(
            "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent",
            lambda **kwargs: DummyAgent(),
        )

        result = pipeline.build_manifest_from_text(
            "Test text",
            str(tmp_path),
            engine="llm",
            engine_overrides={"temperature": 0.7, "model": "gpt-3.5-turbo"},
            verbose=False,  # Modo não-verbose
        )

        # Verificar que logs foram chamados (o conteúdo específico pode variar)
        assert mock_line.called
        assert result["status"] == "Awaiting Consolidation"


def test_file_pipeline_with_llm(tmp_path, monkeypatch):
    """Testa pipeline de arquivo com engine LLM"""
    monkeypatch.chdir(tmp_path)

    # Criar arquivo de teste
    test_file = tmp_path / "test.txt"
    test_file.write_text("Sample file content with reference", encoding="utf-8")

    class DummyAgent:
        def extract(self, text):
            return {
                "references": [
                    {
                        "id": 1,
                        "rawString": "test",
                        "referenceType": "web_link",
                        "sourceFormat": "web_content",
                        "sourcePath": "test",
                        "details": {},
                    }
                ]
            }

    monkeypatch.setattr(
        "core.infrastructure.extraction.langchain_agent.LangChainExtractionAgent",
        lambda **kwargs: DummyAgent(),
    )

    result = pipeline.build_manifest_from_file(
        str(test_file),
        str(tmp_path),
        engine="llm",
        engine_overrides={"provider": "openai"},
    )

    assert result["status"] == "Awaiting Consolidation"
    assert "references" in result["knowledgeIndex"]


def test_verbose_report_generation(tmp_path, monkeypatch):
    """Testa geração completa de relatório verbose"""
    from unittest.mock import patch

    monkeypatch.chdir(tmp_path)

    class DummyAgent:
        def extract(self, text):
            return {
                "references": [
                    {
                        "id": 1,
                        "referenceType": "web_link",
                        "rawString": "https://test.com",
                        "sourceFormat": "web_content",
                        "sourcePath": "https://test.com",
                        "details": {},
                    },
                    {
                        "id": 2,
                        "referenceType": "in_text_citation",
                        "rawString": "Author (2024)",
                        "sourceFormat": "text",
                        "sourcePath": "",
                        "details": {},
                    },
                ]
            }

    with patch("core.application.pipeline.summary_panel") as mock_panel:
        monkeypatch.setattr(
            "core.application.pipeline.HeuristicExtractionAgent", lambda: DummyAgent()
        )

        pipeline.build_manifest_from_text(
            "Test content",
            str(tmp_path),
            engine="heuristic",
            verbose=True,  # Verbose ativo
        )

        # Verificar que summary_panel foi chamado com relatório
        mock_panel.assert_called_once()
        call_args = mock_panel.call_args[0]
        assert call_args[0] == "Collect Report"
        assert "Mode:" in call_args[1]  # Verificar conteúdo do relatório
        assert "URLs:" in call_args[1]
