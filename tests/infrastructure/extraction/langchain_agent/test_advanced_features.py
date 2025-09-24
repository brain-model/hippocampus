import os
from unittest.mock import Mock, patch

import pytest

from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


# === RETRY LOGIC TESTS ===
class TestRetryLogic:
    """Testa lógica de retry para chamadas LLM"""

    def test_resolve_retries_from_env(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.retries = None

        with patch.dict(os.environ, {"HIPPO_LLM_RETRIES": "3"}):
            result = agent._resolve_retries(cfg)
            assert result == 3

    def test_resolve_retries_from_override(self):
        agent = LangChainExtractionAgent(cfg_override={"retries": 5})
        cfg = Mock()
        cfg.retries = None

        result = agent._resolve_retries(cfg)
        assert result == 5

    def test_resolve_retries_from_config(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.retries = 2

        result = agent._resolve_retries(cfg)
        assert result == 2

    def test_resolve_retries_invalid_env_value(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.retries = None

        with patch.dict(os.environ, {"HIPPO_LLM_RETRIES": "invalid"}):
            result = agent._resolve_retries(cfg)
            assert result == 0

    def test_resolve_retries_negative_values(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.retries = -5

        result = agent._resolve_retries(cfg)
        assert result == 0  # Should be clamped to 0

    def test_call_with_retries_success_first_attempt(self):
        agent = LangChainExtractionAgent()

        # Mock model with invoke method
        model = Mock()
        mock_response = Mock()
        mock_response.content = "test content"
        model.invoke.return_value = mock_response

        with patch.object(
            agent, "_extract_tokens", return_value={"prompt": 10, "completion": 5}
        ):
            content, tokens = agent._call_with_retries(model, "test prompt", retries=3)

            assert content == "test content"
            assert tokens == {"prompt": 10, "completion": 5}
            model.invoke.assert_called_once_with("test prompt")

    def test_call_with_retries_success_after_failures(self):
        agent = LangChainExtractionAgent()

        model = Mock()
        mock_response = Mock()
        mock_response.content = "success content"

        # First two calls fail, third succeeds
        model.invoke.side_effect = [
            RuntimeError("Network error"),
            TimeoutError("Request timeout"),
            mock_response,
        ]

        with patch.object(agent, "_extract_tokens", return_value=None):
            content, tokens = agent._call_with_retries(model, "test prompt", retries=3)

            assert content == "success content"
            assert tokens is None
            assert model.invoke.call_count == 3

    def test_call_with_retries_all_attempts_fail(self):
        agent = LangChainExtractionAgent()

        model = Mock()
        model.invoke.side_effect = RuntimeError("Persistent error")

        with pytest.raises(RuntimeError, match="Persistent error"):
            agent._call_with_retries(model, "test prompt", retries=2)

        assert model.invoke.call_count == 3  # 1 + 2 retries

    def test_call_with_retries_legacy_predict_method(self):
        agent = LangChainExtractionAgent()

        # Mock model without invoke method, using predict
        model = Mock()
        del model.invoke  # Remove invoke attribute
        model.predict.return_value = "legacy content"

        content, tokens = agent._call_with_retries(model, "test prompt", retries=0)

        assert content == "legacy content"
        assert tokens is None
        model.predict.assert_called_once_with("test prompt")

    def test_call_with_retries_fallback_to_str(self):
        agent = LangChainExtractionAgent()

        model = Mock()
        mock_response = Mock()
        mock_response.content = None
        mock_response.text = None
        # Will fallback to str(mock_response)

        model.invoke.return_value = mock_response

        with patch.object(agent, "_extract_tokens", return_value=None):
            content, tokens = agent._call_with_retries(model, "test prompt", retries=0)

            assert content == str(mock_response)
            assert tokens is None


# === TOKEN EXTRACTION TESTS ===
class TestTokenExtraction:
    """Testa extração de tokens de resposta LLM"""

    def test_extract_tokens_usage_metadata(self):
        agent = LangChainExtractionAgent()

        msg = Mock()
        msg.usage_metadata = {"input_tokens": 50, "output_tokens": 30}

        result = agent._extract_tokens(msg)

        assert result == {"prompt": 50, "completion": 30}

    def test_extract_tokens_response_metadata(self):
        agent = LangChainExtractionAgent()

        msg = Mock()
        msg.usage_metadata = None
        msg.response_metadata = {
            "token_usage": {"prompt_tokens": 100, "completion_tokens": 75}
        }

        result = agent._extract_tokens(msg)

        assert result == {"prompt": 100, "completion": 75}

    def test_extract_tokens_alternative_field_names(self):
        agent = LangChainExtractionAgent()

        msg = Mock()
        msg.usage_metadata = {"prompt_tokens": 25, "completion_tokens": 15}

        result = agent._extract_tokens(msg)

        assert result == {"prompt": 25, "completion": 15}

    def test_extract_tokens_no_metadata(self):
        agent = LangChainExtractionAgent()

        msg = Mock()
        msg.usage_metadata = None
        msg.response_metadata = None

        result = agent._extract_tokens(msg)

        assert result is None

    def test_extract_tokens_invalid_metadata_format(self):
        agent = LangChainExtractionAgent()

        msg = Mock()
        msg.usage_metadata = "invalid"  # Not a dict
        msg.response_metadata = {"token_usage": "also invalid"}

        result = agent._extract_tokens(msg)

        assert result is None

    def test_extract_tokens_missing_token_fields(self):
        agent = LangChainExtractionAgent()

        msg = Mock()
        msg.usage_metadata = {"other_field": 123}  # Missing token fields

        result = agent._extract_tokens(msg)

        assert result == {"prompt": 0, "completion": 0}


# === API KEY RESOLUTION TESTS ===
class TestApiKeyResolution:
    """Testa resolução de chaves de API por provedor"""

    def test_resolve_api_key_openai(self):
        agent = LangChainExtractionAgent()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            result = agent._resolve_api_key("openai")
            assert result == "sk-test"

    def test_resolve_api_key_gemini(self):
        agent = LangChainExtractionAgent()

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "gemini-key"}, clear=True):
            result = agent._resolve_api_key("gemini")
            assert result == "gemini-key"

    def test_resolve_api_key_claude(self):
        agent = LangChainExtractionAgent()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "claude-key"}, clear=True):
            result = agent._resolve_api_key("claude")
            assert result == "claude-key"

    def test_resolve_api_key_deepseek(self):
        agent = LangChainExtractionAgent()

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "deepseek-key"}, clear=True):
            result = agent._resolve_api_key("deepseek")
            assert result == "deepseek-key"

    def test_resolve_api_key_missing(self):
        agent = LangChainExtractionAgent()

        with patch.dict(os.environ, {}, clear=True):
            result = agent._resolve_api_key("openai")
            assert result is None
