from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from core.cli.exit_codes import get_exit_code_for_exception
from core.domain.interfaces import ExtractionAgent
from core.infrastructure.config.manager import ConfigManager
from core.infrastructure.logging.structured import get_logger
from core.reliability.retry import (
    DEFAULT_BACKOFF_BASE_S,
    DEFAULT_BACKOFF_MAX_S,
    DEFAULT_JITTER_S,
    is_permanent_error,
    retry_call,
)


@dataclass
class LLMConfig:
    provider: str
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout_s: int | None = None
    base_url: str | None = None


class LangChainExtractionAgent(ExtractionAgent):
    def __init__(
        self,
        scope_precedence: tuple[str, ...] = ("local", "global"),
        cfg_override: dict[str, Any] | None = None,
    ) -> None:
        self.scope_precedence = scope_precedence
        self.cfg_override: dict[str, Any] = cfg_override or {}
        self.last_provider: str | None = None
        self.last_model: str | None = None
        self.last_tokens: dict[str, int] | None = None
        self.last_extract_latency_ms: int | None = None

    def _resolve_cfg(self) -> LLMConfig:
        # resolve with precedence: overrides (CLI) > local > global
        override_items = (self.cfg_override or {}).items()
        acc: dict[str, Any] = {k: v for k, v in override_items if v is not None}
        for scope in self.scope_precedence:
            mgr = ConfigManager(scope)
            eng = mgr.get("engine", {}) or {}
            if isinstance(eng, dict):
                self._merge_engine_settings(acc, eng)
        provider = acc.get("provider") or "openai"
        return LLMConfig(
            provider=provider,
            model=acc.get("model"),
            temperature=acc.get("temperature"),
            max_tokens=acc.get("max_tokens"),
            timeout_s=acc.get("timeout_s"),
            base_url=acc.get("base_url"),
        )

    def _merge_engine_settings(self, acc: dict[str, Any], eng: dict[str, Any]) -> None:
        for k, v in eng.items():
            if v is not None and k not in acc:
                acc[k] = v

    def _make_model(self, cfg: LLMConfig, api_key: str | None) -> Any:
        provider = cfg.provider
        if provider in {"openai", "deepseek"}:
            return self._create_openai_like(cfg, api_key)
        if provider == "gemini":
            return self._create_gemini(cfg, api_key)
        if provider == "claude":
            return self._create_claude(cfg, api_key)
        raise ValueError(f"unsupported provider: {provider}")

    _ERR_MISSING_KEY = "missing API key for provider"

    def _missing_key_error(self, provider: str, env_var: str) -> RuntimeError:
        hint = (
            f"Missing API key for provider '{provider}'. "
            f"Set via 'hippo set api.{provider}.key=...' or export {env_var}."
        )
        return RuntimeError(hint)

    def _create_openai_like(self, cfg: LLMConfig, api_key: str | None) -> Any:
        try:
            from langchain_openai import ChatOpenAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "Dependência LLM ausente (OpenAI compat). "
                "Reinstale o pacote ou sincronize o ambiente (uv/pip) "
                "para garantir instalação completa."
            ) from e

        if not api_key:
            raise RuntimeError(f"Missing API key for provider '{cfg.provider}'")

        timeout_val = cfg.timeout_s
        if timeout_val is not None and isinstance(timeout_val, str):
            try:
                timeout_val = int(timeout_val)
            except ValueError:
                timeout_val = float(timeout_val)
        return ChatOpenAI(
            model=cfg.model or self._get_default_model(cfg.provider),
            temperature=cfg.temperature or 0.2,
            timeout=timeout_val,
            max_tokens=cfg.max_tokens,
            base_url=cfg.base_url or self._get_default_base_url(cfg.provider),
            api_key=api_key,
        )

    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider."""
        if provider == "deepseek":
            return "deepseek-chat"
        return "gpt-4o-mini"

    def _get_default_base_url(self, provider: str) -> str | None:
        """Get default base URL for provider."""
        if provider == "deepseek":
            return "https://api.deepseek.com/v1"
        return None

    def _create_gemini(self, cfg: LLMConfig, api_key: str | None) -> Any:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "Dependência LLM ausente (Google Gemini). "
                "Reinstale o pacote ou sincronize o ambiente (uv/pip) "
                "para garantir instalação completa."
            ) from e

        api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise self._missing_key_error("gemini", "GOOGLE_API_KEY")
        timeout_val: float | int = cfg.timeout_s or 60
        if isinstance(timeout_val, str):
            try:
                timeout_val = int(timeout_val)
            except ValueError:
                timeout_val = float(timeout_val)
        return ChatGoogleGenerativeAI(
            model=cfg.model or "gemini-1.5-pro",
            temperature=cfg.temperature or 0.2,
            max_output_tokens=cfg.max_tokens,
            timeout=timeout_val,
            api_key=api_key,
        )

    def _create_claude(self, cfg: LLMConfig, api_key: str | None) -> Any:
        try:
            from langchain_anthropic import ChatAnthropic  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "Dependência LLM ausente (Anthropic Claude). "
                "Reinstale o pacote ou sincronize o ambiente (uv/pip) "
                "para garantir instalação completa."
            ) from e

        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise self._missing_key_error("claude", "ANTHROPIC_API_KEY")
        timeout_val: float | int = cfg.timeout_s or 60
        if isinstance(timeout_val, str):
            try:
                timeout_val = int(timeout_val)
            except ValueError:
                timeout_val = float(timeout_val)
        return ChatAnthropic(
            model=cfg.model or "claude-3-5-sonnet-latest",
            temperature=cfg.temperature or 0.2,
            max_tokens=cfg.max_tokens,
            timeout=timeout_val,
            api_key=api_key,
        )

    def _build_prompt(self, text: str) -> str:
        # Load Markdown prompt exclusively from package resources
        from pathlib import Path

        base = Path(__file__).resolve().parents[2] / "resources" / "prompts"
        p = base / "extract_references_en.md"
        return p.read_text(encoding="utf-8") + "\n\n" + text

    def extract(self, text: str) -> dict:
        try:
            cfg = self._resolve_cfg()
            api_key = self._resolve_api_key(cfg.provider)
            model = self._make_model(cfg, api_key)
            prompt = self._build_prompt(text)
            self._update_last_metadata(cfg, model, prompt)
            data = self._extract_json_from_content(self._last_content)
            if (
                not isinstance(data, dict)
                or "references" not in data
                or not isinstance(data.get("references"), list)
            ):
                raise RuntimeError("LLM output missing 'references' list")
            return self._normalize_output(data)
        except Exception as e:  # noqa: BLE001
            provider = getattr(locals().get("cfg"), "provider", None)
            self._handle_provider_errors(e, provider=provider)

    def _update_last_metadata(self, cfg, model, prompt):
        start = __import__("time").time()
        content, tokens = self._call_with_retries(
            model, prompt, retries=self._resolve_retries(cfg)
        )
        self._last_content = content
        self.last_provider = cfg.provider
        self.last_model = cfg.model or self._default_model_for_provider(cfg.provider)
        self.last_tokens = tokens
        self.last_extract_latency_ms = int((__import__("time").time() - start) * 1000)

    def _default_model_for_provider(self, provider):
        return {
            "deepseek": "deepseek-chat",
            "openai": "gpt-4o-mini",
            "gemini": "gemini-1.5-pro",
            "claude": "claude-3-5-sonnet-latest",
        }.get(provider, "unknown")

    def _extract_json_from_content(self, content):
        try:
            return json.loads(content)
        except Exception:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or start >= end:
                raise RuntimeError("LLM did not return JSON content")
            return json.loads(content[start : end + 1])

    def _handle_provider_errors(self, e, provider: str | None = None):
        # Initialize logger for error handling
        logger = get_logger(__name__)

        # Log error details with structured information
        error_type = type(e).__name__
        exit_code = get_exit_code_for_exception(e)

        logger.debug(
            f"Provider error occurred: {error_type}",
            provider=provider or "unknown",
            error_type=error_type,
            exit_code=int(exit_code),
            error_message=str(e),
        )

        if isinstance(e, TimeoutError):
            logger.warning(
                "LLM request timed out", provider=provider, timeout_error=True
            )
            # Preserve native timeout semantics expected by callers/tests
            raise e
        # Propagate explicit argument/usage errors without wrapping
        if isinstance(e, ValueError):
            logger.error(
                f"Value error in LLM call: {e}",
                provider=provider,
                error_type=error_type,
            )
            raise e
        # Prefer checks/fallbacks for the current provider when known
        if provider == "openai":
            self._check_openai_error(e)
        elif provider == "gemini":
            self._check_gemini_error(e)
        elif provider == "claude":
            self._check_anthropic_error(e)
        else:
            # Unknown: try all
            self._check_openai_error(e)
            self._check_gemini_error(e)
            self._check_anthropic_error(e)

        # Log generic fallback error
        logger.error(
            f"Unexpected LLM provider error: {e}",
            provider=provider,
            error_type=error_type,
            exit_code=int(exit_code),
        )
        # Generic fallback
        raise RuntimeError(f"❌ Erro inesperado na chamada ao provedor LLM: {e}") from e

    def _check_openai_error(self, e) -> None:
        try:
            import openai  # type: ignore

            rate_limit_err = getattr(openai, "RateLimitError", None)
            auth_err = getattr(openai, "AuthenticationError", None)
            if rate_limit_err is not None and isinstance(e, rate_limit_err):
                msg = (
                    "❌ Erro: Limite de uso da API OpenAI excedido.\n"
                    "Verifique seu plano, limites e billing em "
                    "https://platform.openai.com/account/usage\n"
                    f"Detalhes: {e}"
                )
                raise RuntimeError(msg) from e
            if auth_err is not None and isinstance(e, auth_err):
                msg = (
                    "❌ Erro: Chave de API OpenAI inválida ou ausente.\n"
                    "Verifique se a variável OPENAI_API_KEY está correta e ativa.\n"
                    f"Detalhes: {e}"
                )
                raise RuntimeError(msg) from e
        except Exception:
            # Continue to fallback by class name
            pass
        # Fallback when SDK types are not present but tests/mocks
        # raise similarly named errors
        name = type(e).__name__
        if name in {"RateLimitError", "RateLimit"}:
            msg = (
                "❌ Erro: Limite de uso da API OpenAI excedido.\n"
                "Verifique seu plano, limites e billing em "
                "https://platform.openai.com/account/usage\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e
        if name in {"AuthenticationError", "AuthError"}:
            msg = (
                "❌ Erro: Chave de API OpenAI inválida ou ausente.\n"
                "Verifique se a variável OPENAI_API_KEY está correta e ativa.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e

    def _check_gemini_error(self, e) -> None:
        try:
            from google.api_core import exceptions as gexc  # type: ignore

            res_exhausted = getattr(gexc, "ResourceExhausted", None)
            perm_denied = getattr(gexc, "PermissionDenied", None)
            deadline_exceeded = getattr(gexc, "DeadlineExceeded", None)
            if res_exhausted is not None and isinstance(e, res_exhausted):
                msg = (
                    "❌ Erro: Limite de uso/quotas do Google Gemini excedido.\n"
                    "Verifique quotas e billing no Console.\n"
                    f"Detalhes: {e}"
                )
                raise RuntimeError(msg) from e
            if perm_denied is not None and isinstance(e, perm_denied):
                msg = (
                    "❌ Erro: Permissão negada para Google Gemini.\n"
                    "Verifique a chave (GOOGLE_API_KEY) e permissões do projeto.\n"
                    f"Detalhes: {e}"
                )
                raise RuntimeError(msg) from e
            if deadline_exceeded is not None and isinstance(e, deadline_exceeded):
                msg = (
                    "⏱️ Timeout na chamada ao Google Gemini.\n"
                    "Considere aumentar 'engine.timeout_s' ou reduzir a entrada.\n"
                    f"Detalhes: {e}"
                )
                raise RuntimeError(msg) from e
        except Exception:
            # Continue to fallback by class name
            pass
        # Fallback by class name for mocked environments
        name = type(e).__name__
        if name == "ResourceExhausted":
            msg = (
                "❌ Erro: Limite de uso/quotas do Google Gemini excedido.\n"
                "Verifique quotas e billing no Console.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e
        if name == "PermissionDenied":
            msg = (
                "❌ Erro: Permissão negada para Google Gemini.\n"
                "Verifique a chave (GOOGLE_API_KEY) e permissões do projeto.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e
        if name == "DeadlineExceeded":
            msg = (
                "⏱️ Timeout na chamada ao Google Gemini.\n"
                "Considere aumentar 'engine.timeout_s' ou reduzir a entrada.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e

    def _check_anthropic_error(self, e) -> None:
        try:
            import anthropic  # type: ignore

            rate_limit_err = getattr(anthropic, "RateLimitError", None)
            auth_err = getattr(anthropic, "AuthenticationError", None)
            if rate_limit_err is not None and isinstance(e, rate_limit_err):
                msg = (
                    "❌ Erro: Limite de uso da API Anthropic (Claude) excedido.\n"
                    "Verifique seu plano e limites no dashboard.\n"
                    f"Detalhes: {e}"
                )
                raise RuntimeError(msg) from e
            if auth_err is not None and isinstance(e, auth_err):
                msg = (
                    "❌ Erro: Chave de API Anthropic (Claude) inválida ou ausente.\n"
                    "Verifique a variável ANTHROPIC_API_KEY.\n"
                    f"Detalhes: {e}"
                )
                raise RuntimeError(msg) from e
        except Exception:
            # Continue to fallback by class name
            pass
        # Fallback by class name
        name = type(e).__name__
        if name in {"RateLimitError", "RateLimit"}:
            msg = (
                "❌ Erro: Limite de uso da API Anthropic (Claude) excedido.\n"
                "Verifique seu plano e limites no dashboard.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e
        if name in {"AuthenticationError", "AuthError"}:
            msg = (
                "❌ Erro: Chave de API Anthropic (Claude) inválida ou ausente.\n"
                "Verifique a variável ANTHROPIC_API_KEY.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e

    def _normalize_output(self, data: dict[str, Any]) -> dict[str, Any]:
        refs = data.get("references") or []
        out: list[dict[str, Any]] = []
        for idx, r in enumerate(refs, start=1):
            item = self._normalize_reference_item(r, idx)
            if item is not None:
                out.append(item)
        return {"references": out}

    def _normalize_reference_item(self, r: Any, idx: int) -> dict[str, Any] | None:
        if not isinstance(r, dict):
            return None

        # Check if it's already normalized with required fields
        if self._has_required_reference_fields(r):
            return self._build_normalized_reference(r, idx)

        # Build reference from standard fields
        return self._build_reference_from_standard_fields(r, idx)

    def _has_required_reference_fields(self, r: dict) -> bool:
        required = {
            "rawString",
            "referenceType",
            "sourceFormat",
            "sourcePath",
            "details",
        }
        return required.issubset(r.keys())

    def _build_normalized_reference(self, r: dict, idx: int) -> dict[str, Any]:
        return {
            "id": r.get("id", idx),
            "rawString": r["rawString"],
            "referenceType": r["referenceType"],
            "sourceFormat": r["sourceFormat"],
            "sourcePath": r["sourcePath"],
            "details": r.get("details", {}) or {},
        }

    def _build_reference_from_standard_fields(
        self, r: dict, idx: int
    ) -> dict[str, Any]:
        # Extract standard fields
        title = r.get("title")
        authors = r.get("authors")
        year = r.get("year")
        venue = r.get("venue")
        url = r.get("url")
        doi = self._normalize_doi(r.get("doi"))
        citation = r.get("citation") or r.get("text")

        if not url and doi:
            url = f"https://doi.org/{doi}"

        details = self._build_details_dict(title, authors, year, venue, doi)

        if url:
            return self._build_web_reference(idx, url, details)

        raw = citation or title or ""
        return self._build_text_reference(idx, raw, details)

    def _normalize_doi(self, doi: Any) -> str | None:
        if doi is not None:
            # normalize DOI: trim and remove inner whitespace/newlines
            return re.sub(r"\s+", "", str(doi).strip())
        return None

    def _build_details_dict(
        self, title: Any, authors: Any, year: Any, venue: Any, doi: str | None
    ) -> dict[str, Any]:
        details: dict[str, Any] = {}
        if title:
            details["title"] = title
        if authors:
            details["authors"] = authors
        if year:
            details["year"] = year
        if venue:
            details["venue"] = venue
        if doi:
            details["doi"] = doi
        return details

    def _build_web_reference(self, idx: int, url: str, details: dict) -> dict[str, Any]:
        return {
            "id": idx,
            "rawString": url,
            "referenceType": "web_link",
            "sourceFormat": "web_content",
            "sourcePath": url,
            "details": details,
        }

    def _build_text_reference(
        self, idx: int, raw: str, details: dict
    ) -> dict[str, Any]:
        return {
            "id": idx,
            "rawString": raw,
            "referenceType": "in_text_citation",
            "sourceFormat": "text",
            "sourcePath": "",
            "details": details,
        }

    def _resolve_api_key(self, provider: str) -> str | None:
        for scope in self.scope_precedence:
            key = ConfigManager(scope).get_secret(provider)
            if key:
                return key
        env_map = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        if provider not in env_map:
            raise ValueError(f"unsupported provider: {provider}")
        return os.environ.get(env_map[provider])

    def _resolve_retries(self, cfg: LLMConfig) -> int:
        env_val = os.environ.get("HIPPO_LLM_RETRIES")
        if env_val is not None:
            try:
                return max(0, int(env_val))
            except ValueError:
                return 0
        # cfg_override may include 'retries'
        if "retries" in self.cfg_override and self.cfg_override["retries"] is not None:
            try:
                return max(0, int(self.cfg_override["retries"]))
            except Exception:
                return 0
        return max(0, int(getattr(cfg, "retries", 0) or 0))

    def _call_with_retries(
        self, model: Any, prompt: str, retries: int = 0
    ) -> tuple[str, dict[str, int] | None]:
        attempts = max(1, retries + 1)

        # Initialize logger for trace logging
        logger = get_logger(__name__)
        trace_llm = os.getenv("HIPPO_TRACE_LLM", "false").lower() == "true"

        if trace_llm:
            logger.debug(
                "LLM call initiated",
                prompt_length=len(prompt),
                max_attempts=attempts,
                model_type=type(model).__name__,
            )

        def _invoke_once():
            return self._invoke_model_once(model, prompt, trace_llm, logger)

        def _should_retry(e: Exception) -> bool:
            return self._should_retry_error(e, trace_llm, logger)

        return retry_call(
            _invoke_once,
            attempts,
            DEFAULT_BACKOFF_BASE_S,
            DEFAULT_JITTER_S,
            DEFAULT_BACKOFF_MAX_S,
            _should_retry,
        )

    def _invoke_model_once(
        self, model: Any, prompt: str, trace_llm: bool, logger
    ) -> tuple[str, dict[str, int] | None]:
        invoke = getattr(model, "invoke", None)
        if callable(invoke):
            out = invoke(prompt)
            content = (
                getattr(out, "content", None) or getattr(out, "text", None) or str(out)
            )
            tokens = self._extract_tokens(out)

            if trace_llm:
                logger.debug(
                    "LLM response received",
                    content_length=len(content) if content else 0,
                    tokens=tokens,
                )
        else:
            content = model.predict(prompt)
            tokens = None

            if trace_llm:
                logger.debug(
                    "LLM response received (predict method)",
                    content_length=len(content) if content else 0,
                )
        return content, tokens

    def _should_retry_error(self, e: Exception, trace_llm: bool, logger) -> bool:
        if trace_llm:
            logger.debug(
                "LLM call failed, checking retry",
                error_type=type(e).__name__,
                is_permanent=is_permanent_error(e),
            )
        return not is_permanent_error(e)

    def _extract_tokens(self, msg: Any) -> dict[str, int] | None:
        # Try LangChain's common metadata fields
        usage = getattr(msg, "usage_metadata", None)
        if isinstance(usage, dict):
            pt = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
            ct = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
            return {"prompt": pt, "completion": ct}
        meta = getattr(msg, "response_metadata", None)
        if isinstance(meta, dict):
            tu = meta.get("token_usage") or {}
            if isinstance(tu, dict):
                pt = int(tu.get("prompt_tokens") or 0)
                ct = int(tu.get("completion_tokens") or 0)
                return {"prompt": pt, "completion": ct}
        return None
