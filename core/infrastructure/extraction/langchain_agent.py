from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.domain.interfaces import ExtractionAgent
from core.infrastructure.config.manager import ConfigManager


@dataclass
class LLMConfig:
    provider: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_s: Optional[int] = None
    base_url: Optional[str] = None


class LangChainExtractionAgent(ExtractionAgent):
    def __init__(
        self,
        scope_precedence: tuple[str, ...] = ("local", "global"),
        cfg_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.scope_precedence = scope_precedence
        self.cfg_override: Dict[str, Any] = cfg_override or {}
        self.last_provider: Optional[str] = None
        self.last_model: Optional[str] = None
        self.last_tokens: Optional[Dict[str, int]] = None
        self.last_extract_latency_ms: Optional[int] = None

    def _resolve_cfg(self) -> LLMConfig:
        # resolve with precedence: overrides (CLI) > local > global
        acc: Dict[str, Any] = {k: v for k, v in (self.cfg_override or {}).items() if v is not None}
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

    def _merge_engine_settings(self, acc: Dict[str, Any], eng: Dict[str, Any]) -> None:
        for k, v in eng.items():
            if v is not None and k not in acc:
                acc[k] = v

    def _make_model(self, cfg: LLMConfig, api_key: Optional[str]) -> Any:
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

    def _create_openai_like(self, cfg: LLMConfig, api_key: Optional[str]) -> Any:
        try:
            from langchain_openai import ChatOpenAI  # type: ignore
        except Exception as e:  # pragma: no cover - optional extra
            raise ImportError("Install extra 'llm' to use OpenAI-compatible providers") from e

        base_url = cfg.base_url
        if cfg.provider == "deepseek" and not base_url:
            base_url = "https://api.deepseek.com/v1"
        env_var = "DEEPSEEK_API_KEY" if cfg.provider == "deepseek" else "OPENAI_API_KEY"
        api_key = api_key or os.environ.get(env_var)
        if not api_key:
            raise self._missing_key_error(cfg.provider, env_var)
        timeout_val: float | int = cfg.timeout_s or 60
        if isinstance(timeout_val, str):
            try:
                timeout_val = int(timeout_val)
            except ValueError:
                timeout_val = float(timeout_val)
        return ChatOpenAI(
            model=cfg.model or ("deepseek-chat" if cfg.provider == "deepseek" else "gpt-4o-mini"),
            temperature=cfg.temperature or 0.2,
            timeout=timeout_val,
            max_tokens=cfg.max_tokens,
            base_url=base_url,
            api_key=api_key,
        )

    def _create_gemini(self, cfg: LLMConfig, api_key: Optional[str]) -> Any:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
        except Exception as e:  # pragma: no cover - optional extra
            raise ImportError("Install extra 'llm' to use Google Gemini provider") from e

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

    def _create_claude(self, cfg: LLMConfig, api_key: Optional[str]) -> Any:
        try:
            from langchain_anthropic import ChatAnthropic  # type: ignore
        except Exception as e:  # pragma: no cover - optional extra
            raise ImportError("Install extra 'llm' to use Anthropic Claude provider") from e

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
            self._handle_provider_errors(e, provider=cfg.provider)

    def _update_last_metadata(self, cfg, model, prompt):
        start = __import__("time").time()
        content, tokens = self._call_with_retries(model, prompt, retries=self._resolve_retries(cfg))
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
            return json.loads(content[start:end + 1])

    def _handle_provider_errors(self, e, provider: Optional[str] = None):
        if isinstance(e, TimeoutError):
            # Preserve native timeout semantics expected by callers/tests
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
        # Fallback when SDK types are not present but tests/mocks raise similarly named errors
        name = type(e).__name__
        if name == "RateLimitError" or name == "RateLimit":
            msg = (
                "❌ Erro: Limite de uso da API OpenAI excedido.\n"
                "Verifique seu plano, limites e billing em "
                "https://platform.openai.com/account/usage\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e
        if name == "AuthenticationError" or name == "AuthError":
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
        if name == "RateLimitError" or name == "RateLimit":
            msg = (
                "❌ Erro: Limite de uso da API Anthropic (Claude) excedido.\n"
                "Verifique seu plano e limites no dashboard.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e
        if name == "AuthenticationError" or name == "AuthError":
            msg = (
                "❌ Erro: Chave de API Anthropic (Claude) inválida ou ausente.\n"
                "Verifique a variável ANTHROPIC_API_KEY.\n"
                f"Detalhes: {e}"
            )
            raise RuntimeError(msg) from e

    def _normalize_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        refs = data.get("references") or []
        out: list[Dict[str, Any]] = []
        for idx, r in enumerate(refs, start=1):
            item = self._normalize_reference_item(r, idx)
            if item is not None:
                out.append(item)
        return {"references": out}

    def _normalize_reference_item(self, r: Any, idx: int) -> Optional[Dict[str, Any]]:
        if not isinstance(r, dict):
            return None
        required = {"rawString", "referenceType", "sourceFormat", "sourcePath", "details"}
        if required.issubset(r.keys()):
            return {
                "id": r.get("id", idx),
                "rawString": r["rawString"],
                "referenceType": r["referenceType"],
                "sourceFormat": r["sourceFormat"],
                "sourcePath": r["sourcePath"],
                "details": r.get("details", {}) or {},
            }

        title = r.get("title")
        authors = r.get("authors")
        year = r.get("year")
        venue = r.get("venue")
        url = r.get("url")
        doi = r.get("doi")
        citation = r.get("citation") or r.get("text")

        if not url and doi:
            url = f"https://doi.org/{doi}".strip()

        details: Dict[str, Any] = {}
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

        if url:
            return {
                "id": idx,
                "rawString": url,
                "referenceType": "web_link",
                "sourceFormat": "web_content",
                "sourcePath": url,
                "details": details,
            }
        raw = citation or title or ""
        return {
            "id": idx,
            "rawString": raw,
            "referenceType": "in_text_citation",
            "sourceFormat": "text",
            "sourcePath": "",
            "details": details,
        }

    def _resolve_api_key(self, provider: str) -> Optional[str]:
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
    ) -> tuple[str, Dict[str, int] | None]:
        attempts = max(1, retries + 1)
        last_err: Exception | None = None
        for _ in range(attempts):
            try:
                invoke = getattr(model, "invoke", None)
                if callable(invoke):
                    out = invoke(prompt)
                    content = (
                        getattr(out, "content", None)
                        or getattr(out, "text", None)
                        or str(out)
                    )
                    tokens = self._extract_tokens(out)
                else:
                    content = model.predict(prompt)
                    tokens = None
                return content, tokens
            except Exception as e:  # noqa: BLE001
                last_err = e
        assert last_err is not None
        raise last_err

    def _extract_tokens(self, msg: Any) -> Dict[str, int] | None:
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
