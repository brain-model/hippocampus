from unittest.mock import MagicMock, patch

import pytest

import core.infrastructure.config.manager as cfg_manager
from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


class DummyMsg:
    def __init__(self, text='{"references": []}'):
        self.text = text
        self.response_metadata = {
            "token_usage": {"prompt_tokens": 1, "completion_tokens": 1}
        }


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    for k in ["DEEPSEEK_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(k, raising=False)
    yield


def test_deepseek_uses_base_url_and_env_key(monkeypatch):
    # Arrange: set DeepSeek key in env
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek")

    # Mock ChatOpenAI class and capture init kwargs
    created = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            created.update(kwargs)

        def invoke(self, prompt):
            return DummyMsg()

    with patch.dict(
        "sys.modules", {"langchain_openai": MagicMock(ChatOpenAI=FakeChatOpenAI)}
    ):
        # Ensure ConfigManager does not return any stored secret so env var is used
        monkeypatch.setattr(
            cfg_manager.ConfigManager, "get_secret", lambda self, provider: None
        )
        agent = LangChainExtractionAgent(
            cfg_override={"provider": "deepseek", "model": "deepseek-chat"}
        )
        # Act: extract minimal JSON
        out = agent.extract("minimal input")

    # Assert
    assert out == {"references": []}
    assert created.get("base_url") == "https://api.deepseek.com/v1"
    assert created.get("api_key") == "sk-deepseek"
    assert created.get("model") == "deepseek-chat"
