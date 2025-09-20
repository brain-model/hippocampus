import pytest
from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent, LLMConfig

# Testa erro de configuração inválida
def test_invalid_provider_raises(monkeypatch):
    agent = LangChainExtractionAgent(cfg_override={"provider": None})
    cfg = agent._resolve_cfg()
    assert cfg.provider == "openai"  # fallback

# Testa erro de timeout
def test_extract_timeout(monkeypatch):
    agent = LangChainExtractionAgent()
    def fake_invoke(_):
        raise TimeoutError("timeout")
    monkeypatch.setattr(agent, "_make_model", lambda cfg, key: type("FakeModel", (), {"invoke": staticmethod(fake_invoke)})())
    with pytest.raises(TimeoutError):
        agent.extract("texto qualquer")

# Testa erro de JSON inválido
def test_extract_invalid_json(monkeypatch):
    agent = LangChainExtractionAgent()
    def fake_invoke(_):
        return "{invalid_json:}"
    monkeypatch.setattr(agent, "_make_model", lambda cfg, key: type("FakeModel", (), {"invoke": staticmethod(fake_invoke)})())
    with pytest.raises(Exception):
        agent.extract("texto qualquer")
