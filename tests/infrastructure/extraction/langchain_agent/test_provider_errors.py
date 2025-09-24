import types
from unittest.mock import patch

import pytest

from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


class Boom(Exception):
    pass


class FakeModel:
    def __init__(self, exc: Exception):
        self._exc = exc

    def invoke(self, prompt: str):
        raise self._exc


@pytest.fixture(autouse=True)
def patch_prompt_and_key(monkeypatch):
    monkeypatch.setattr(
        LangChainExtractionAgent, "_build_prompt", lambda self, text: "X"
    )
    monkeypatch.setattr(
        LangChainExtractionAgent, "_resolve_api_key", lambda self, p: "k"
    )


def _make_agent_with_exc(exc: Exception) -> LangChainExtractionAgent:
    agent = LangChainExtractionAgent(cfg_override={"provider": "openai"})
    agent._make_model = lambda cfg, key: FakeModel(exc)  # type: ignore[attr-defined]
    return agent


def test_openai_rate_limit_maps_to_runtimeerror(monkeypatch):
    openai_mod = types.ModuleType("openai")

    class RateLimitError(Exception):
        pass

    openai_mod.RateLimitError = RateLimitError
    with patch.dict("sys.modules", {"openai": openai_mod}):
        agent = _make_agent_with_exc(RateLimitError("limit"))
        with pytest.raises(RuntimeError) as ei:
            agent.extract("txt")
        assert "OpenAI" in str(ei.value)
        assert "Limite" in str(ei.value)


def test_openai_auth_error_maps_to_runtimeerror(monkeypatch):
    openai_mod = types.ModuleType("openai")

    class AuthenticationError(Exception):
        pass

    openai_mod.AuthenticationError = AuthenticationError
    with patch.dict("sys.modules", {"openai": openai_mod}):
        agent = _make_agent_with_exc(AuthenticationError("bad key"))
        with pytest.raises(RuntimeError) as ei:
            agent.extract("txt")
        assert "Chave de API OpenAI" in str(ei.value)


def test_gemini_permission_denied(monkeypatch):
    # Build google.api_core.exceptions module tree
    google_mod = types.ModuleType("google")
    api_core_mod = types.ModuleType("google.api_core")
    exc_mod = types.ModuleType("google.api_core.exceptions")

    class PermissionDenied(Exception):
        pass

    exc_mod.PermissionDenied = PermissionDenied
    with patch.dict(
        "sys.modules",
        {
            "google": google_mod,
            "google.api_core": api_core_mod,
            "google.api_core.exceptions": exc_mod,
        },
    ):
        agent = LangChainExtractionAgent(cfg_override={"provider": "gemini"})
        agent._make_model = lambda cfg, key: FakeModel(PermissionDenied("no perms"))  # type: ignore
        with pytest.raises(RuntimeError) as ei:
            agent.extract("txt")
        assert "Permissão negada" in str(ei.value)


def test_anthropic_auth_error(monkeypatch):
    anthropic_mod = types.ModuleType("anthropic")

    class AuthenticationError(Exception):
        pass

    anthropic_mod.AuthenticationError = AuthenticationError
    with patch.dict("sys.modules", {"anthropic": anthropic_mod}):
        agent = LangChainExtractionAgent(cfg_override={"provider": "claude"})
        agent._make_model = lambda cfg, key: FakeModel(AuthenticationError("bad"))  # type: ignore
        with pytest.raises(RuntimeError) as ei:
            agent.extract("txt")
        assert "Anthropic" in str(ei.value)


def test_timeout_error_propagates(monkeypatch):
    agent = _make_agent_with_exc(TimeoutError("t"))
    with pytest.raises(TimeoutError):
        agent.extract("txt")
