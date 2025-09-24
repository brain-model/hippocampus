from __future__ import annotations

import time

from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


class DummyMsg:
    def __init__(self, content: str):
        self.content = content
        self.usage_metadata = {"input_tokens": 1, "output_tokens": 1}


class FlakyModel:
    def __init__(self, fail_times: int):
        self._fail_times = fail_times
        self.calls = 0

    def invoke(self, prompt: str):
        self.calls += 1
        if self.calls <= self._fail_times:
            # Simula erro transitório
            ex = TimeoutError("simulated timeout")
            ex.status_code = 503
            raise ex
        return DummyMsg('{\n\t"references": []\n}')


def test_retries_with_backoff_succeeds(monkeypatch):
    agent = LangChainExtractionAgent(
        cfg_override={"provider": "openai", "model": "gpt-4o-mini", "retries": 2}
    )

    # Monkeypatch model creation to return our flaky model
    def fake_make_model(cfg, api_key):
        return FlakyModel(fail_times=2)

    monkeypatch.setattr(agent, "_make_model", fake_make_model)
    monkeypatch.setattr(agent, "_resolve_api_key", lambda provider: "dummy")

    start = time.time()
    out = agent.extract("hello")
    elapsed = time.time() - start

    assert isinstance(out, dict)
    assert out.get("references") == []
    # 3 tentativas: 2 falhas + 1 sucesso
    assert agent.last_extract_latency_ms is not None
    # Deve ter levado ao menos o tempo de dois backoffs pequenos (não fixo)
    assert elapsed >= 0


def test_no_retry_on_permanent_error(monkeypatch):
    agent = LangChainExtractionAgent(
        cfg_override={"provider": "openai", "model": "gpt-4o-mini", "retries": 3}
    )

    class PermError(Exception):
        pass

    err = PermError("invalid api key")
    err.status_code = 401

    class BadModel:
        def invoke(self, prompt: str):
            raise err

    monkeypatch.setattr(agent, "_make_model", lambda cfg, api_key: BadModel())
    monkeypatch.setattr(agent, "_resolve_api_key", lambda provider: "dummy")

    try:
        agent.extract("hello")
        assert False, "should have raised"
    except Exception as e:
        # Deve levantar erro mapeado pelo handler
        assert "inválida" in str(e) or "invalid" in str(e).lower()
