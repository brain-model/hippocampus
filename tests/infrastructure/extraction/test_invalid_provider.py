from __future__ import annotations

import pytest

from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


def test_invalid_provider_raises_value_error(monkeypatch):
    agent = LangChainExtractionAgent(cfg_override={"provider": "nao-suportado"})
    # Força o fluxo até resolver API key
    with pytest.raises(ValueError, match="unsupported provider"):
        agent.extract("hello")
