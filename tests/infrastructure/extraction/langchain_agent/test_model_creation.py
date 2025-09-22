import os
import pytest
from unittest.mock import Mock, patch

from core.infrastructure.extraction.langchain_agent import LangChainExtractionAgent


# === MOCK MODEL CREATION TESTS ===
class TestMakeModel:
    """Testa criação de modelos para diferentes provedores"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    @patch("langchain_openai.ChatOpenAI")
    def test_make_model_openai_success(self, mock_chat_openai):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "openai"
        cfg.model = "gpt-4"
        cfg.temperature = 0.5
        cfg.timeout_s = 30
        cfg.max_tokens = 1000
        cfg.base_url = None

        agent._make_model(cfg, None)

        mock_chat_openai.assert_called_once_with(
            model="gpt-4",
            temperature=0.5,
            timeout=30,
            max_tokens=1000,
            base_url=None,
            api_key="sk-test"
        )

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-deepseek"})
    @patch("langchain_openai.ChatOpenAI")
    def test_make_model_deepseek_default_base_url(self, mock_chat_openai):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "deepseek"
        cfg.model = None
        cfg.temperature = None
        cfg.timeout_s = None
        cfg.max_tokens = None
        cfg.base_url = None

        agent._make_model(cfg, None)

        mock_chat_openai.assert_called_once_with(
            model="deepseek-chat",
            temperature=0.2,
            timeout=60,
            max_tokens=None,
            base_url="https://api.deepseek.com/v1",
            api_key="sk-deepseek"
        )

    def test_make_model_unsupported_provider(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "unsupported"

        with pytest.raises(ValueError, match="unsupported provider: unsupported"):
            agent._make_model(cfg, None)

    def test_missing_key_error_openai(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "openai"
        cfg.model = "gpt-4"
        cfg.temperature = 0.5
        cfg.timeout_s = 30
        cfg.max_tokens = 1000
        cfg.base_url = None

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="Missing API key for provider 'openai'"):
                agent._make_model(cfg, None)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("langchain_google_genai.ChatGoogleGenerativeAI")
    def test_make_model_gemini_success(self, mock_chat_gemini):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "gemini"
        cfg.model = "gemini-1.5-flash"
        cfg.temperature = 0.3
        cfg.timeout_s = "45"  # String timeout
        cfg.max_tokens = 2000

        agent._make_model(cfg, None)

        mock_chat_gemini.assert_called_once_with(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_output_tokens=2000,
            timeout=45,
            api_key="test-key"
        )

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "claude-key"})
    @patch("langchain_anthropic.ChatAnthropic")
    def test_make_model_claude_success(self, mock_chat_claude):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "claude"
        cfg.model = None
        cfg.temperature = None
        cfg.timeout_s = "60.5"  # Float string timeout
        cfg.max_tokens = None

        agent._make_model(cfg, None)

        mock_chat_claude.assert_called_once_with(
            model="claude-3-5-sonnet-latest",
            temperature=0.2,
            max_tokens=None,
            timeout=60.5,
            api_key="claude-key"
        )


# === TIMEOUT CONVERSION TESTS ===
class TestTimeoutHandling:
    """Testa conversão de timeout em diferentes formatos"""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    @patch("langchain_openai.ChatOpenAI")
    def test_timeout_string_int_conversion(self, mock_chat_openai):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "openai"
        cfg.model = "gpt-4"
        cfg.temperature = 0.5
        cfg.timeout_s = "30"  # String integer
        cfg.max_tokens = 1000
        cfg.base_url = None

        agent._make_model(cfg, None)

        # Verify timeout was converted to int
        call_args = mock_chat_openai.call_args[1]
        assert call_args["timeout"] == 30
        assert isinstance(call_args["timeout"], int)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"})
    @patch("langchain_openai.ChatOpenAI")
    def test_timeout_string_float_conversion(self, mock_chat_openai):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "openai"
        cfg.model = "gpt-4"
        cfg.temperature = 0.5
        cfg.timeout_s = "30.5"  # String float
        cfg.max_tokens = 1000
        cfg.base_url = None

        agent._make_model(cfg, None)

        # Verify timeout was converted to float
        call_args = mock_chat_openai.call_args[1]
        assert call_args["timeout"] == pytest.approx(30.5)
        assert isinstance(call_args["timeout"], float)


# === UPDATE METADATA TESTS ===
class TestUpdateLastMetadata:
    """Testa atualização de metadados após chamada LLM"""

    def test_update_last_metadata_success(self):
        agent = LangChainExtractionAgent()

        cfg = Mock()
        cfg.provider = "openai"
        cfg.model = "gpt-4"

        model = Mock()
        prompt = "test prompt"

        # Mock _call_with_retries to return content and tokens
        with patch.object(agent, "_call_with_retries") as mock_call:
            mock_call.return_value = ("test content", 100)
            with patch.object(agent, "_resolve_retries", return_value=3):
                with patch.object(agent, "_default_model_for_provider", return_value="gpt-4o-mini"):

                    agent._update_last_metadata(cfg, model, prompt)

                    assert agent._last_content == "test content"
                    assert agent.last_provider == "openai"
                    assert agent.last_model == "gpt-4"
                    assert agent.last_tokens == 100
                    assert isinstance(agent.last_extract_latency_ms, int)
                    assert agent.last_extract_latency_ms >= 0

    def test_update_last_metadata_default_model(self):
        agent = LangChainExtractionAgent()

        cfg = Mock()
        cfg.provider = "deepseek"
        cfg.model = None  # Should use default

        model = Mock()
        prompt = "test prompt"

        with patch.object(agent, "_call_with_retries") as mock_call:
            mock_call.return_value = ("content", 50)
            with patch.object(agent, "_resolve_retries", return_value=1):
                with patch.object(
                    agent,
                    "_default_model_for_provider",
                    return_value="deepseek-chat"
                ) as mock_default:

                    agent._update_last_metadata(cfg, model, prompt)

                    mock_default.assert_called_once_with("deepseek")
                    assert agent.last_model == "deepseek-chat"


# === DEFAULT MODEL PROVIDER TESTS ===
class TestDefaultModelProvider:
    """Testa mapeamento de modelos padrão por provedor"""

    def test_default_model_deepseek(self):
        agent = LangChainExtractionAgent()
        assert agent._default_model_for_provider("deepseek") == "deepseek-chat"

    def test_default_model_openai(self):
        agent = LangChainExtractionAgent()
        assert agent._default_model_for_provider("openai") == "gpt-4o-mini"

    def test_default_model_gemini(self):
        agent = LangChainExtractionAgent()
        assert agent._default_model_for_provider("gemini") == "gemini-1.5-pro"

    def test_default_model_claude(self):
        agent = LangChainExtractionAgent()
        assert agent._default_model_for_provider("claude") == "claude-3-5-sonnet-latest"


# === IMPORT ERROR TESTS ===
class TestImportErrors:
    """Testa comportamento quando dependências opcionais não estão instaladas"""

    def test_openai_import_error(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "openai"

        with patch("builtins.__import__", side_effect=ImportError("No module")):
            with pytest.raises(
                ImportError,
                match=r"Dependência LLM ausente \(OpenAI compat\)"
            ):
                agent._make_model(cfg, "sk-test")

    def test_gemini_import_error(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "gemini"

        with patch("builtins.__import__", side_effect=ImportError("No module")):
            with pytest.raises(
                ImportError,
                match=r"Dependência LLM ausente \(Google Gemini\)"
            ):
                agent._make_model(cfg, "test-key")

    def test_claude_import_error(self):
        agent = LangChainExtractionAgent()
        cfg = Mock()
        cfg.provider = "claude"

        with patch("builtins.__import__", side_effect=ImportError("No module")):
            with pytest.raises(
                ImportError,
                match=r"Dependência LLM ausente \(Anthropic Claude\)"
            ):
                agent._make_model(cfg, "test-key")
