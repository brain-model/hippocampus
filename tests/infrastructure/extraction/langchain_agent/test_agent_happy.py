from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


def test_extract_valid_json(monkeypatch):
    agent = LangChainExtractionAgent()
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(agent, "_make_model", lambda cfg, key: object())
    monkeypatch.setattr(agent, "_build_prompt", lambda text: text)

    def fake_update_last_metadata(cfg, model, prompt):
        agent._last_content = (
            '{"references": ['
            '{"rawString": "ref1", '
            '"referenceType": "web_link", '
            '"sourceFormat": "web_content", '
            '"sourcePath": "ref1", '
            '"details": {}}'
            "]}"
        )

    monkeypatch.setattr(agent, "_update_last_metadata", fake_update_last_metadata)
    result = agent.extract("texto válido")
    assert "references" in result
    assert isinstance(result["references"], list)
    assert result["references"][0]["rawString"] == "ref1"
