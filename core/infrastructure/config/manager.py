"""Simple configuration manager with local/global scopes and secret handling.

Stores non-secret settings in JSON files and secrets via system keyring when
available, falling back to on-disk storage with restricted permissions.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict

_SECRET_KEY_RE = re.compile(r"^api\.(openai|gemini|claude|deepseek)\.key$")
_SUPPORTED_PROVIDERS = {"openai", "gemini", "claude", "deepseek"}
_SUPPORTED_ENGINE_KEYS = {
    "provider",
    "model",
    "temperature",
    "max_tokens",
    "timeout_s",
    "base_url",
    "retries",
}


def _ensure_parent_permissions(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        try:
            os.chmod(p.parent, 0o700)
        except Exception:
            pass


def _write_secure_json(p: Path, data: Dict[str, Any]) -> None:
    _ensure_parent_permissions(p)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)
    if os.name == "posix":
        try:
            os.chmod(p, 0o600)
        except Exception:
            pass


class ConfigManager:
    """Manage configuration entries in a given scope (local or global)."""

    def __init__(self, scope: str = "local") -> None:
        if scope not in {"local", "global"}:
            raise ValueError("scope must be 'local' or 'global'")
        self.scope = scope
        self.path = self._resolve_path(scope)
        self._cache: Dict[str, Any] | None = None

    def _resolve_path(self, scope: str) -> Path:
        if scope == "local":
            return Path.cwd() / ".hippo" / "config.json"
        # global
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        return base / "hippocampus" / "config.json"

    # Basic load/save
    def _load(self) -> Dict[str, Any]:
        if self._cache is not None:
            return self._cache
        p = self.path
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        else:
            data = {}
        self._cache = data
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        self._cache = data
        _write_secure_json(self.path, data)

    # Public API
    def get(self, key: str, default: Any | None = None) -> Any:
        data = self._load()
        cur = data
        for part in key.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def set(self, key: str, value: Any) -> None:
        if _SECRET_KEY_RE.match(key):
            provider = key.split(".")[1]
            self.set_secret(provider, str(value))
            return
        # validate engine keys and provider values when applicable
        if key.startswith("engine."):
            parts = key.split(".")
            if len(parts) != 2 or parts[1] not in _SUPPORTED_ENGINE_KEYS:
                raise ValueError(
                    "unsupported engine key; allowed: "
                    + ", ".join(sorted(_SUPPORTED_ENGINE_KEYS))
                )
            if parts[1] == "provider" and value not in _SUPPORTED_PROVIDERS:
                raise ValueError(
                    "unsupported provider; allowed: "
                    + ", ".join(sorted(_SUPPORTED_PROVIDERS))
                )
        if key.startswith("api.") and key.count(".") == 1:
            # e.g., api.openai = {...} shouldn't be set directly
            raise ValueError("set keys like 'api.<provider>.key' or via YAML")
        data = self._load()
        cur = data
        parts = key.split(".")
        for part in parts[:-1]:
            if part not in cur or not isinstance(cur[part], dict):
                cur[part] = {}
            cur = cur[part]
        cur[parts[-1]] = value
        self._save(data)

    def set_secret(self, provider: str, api_key: str) -> None:
        service = "hippocampus"
        used_keyring = False
        try:
            import keyring  # type: ignore

            keyring.set_password(service, f"{provider}.api_key:{self.scope}", api_key)
            used_keyring = True
        except Exception:
            used_keyring = False

        if not used_keyring:
            data = self._load()
            secrets = data.setdefault("secrets", {})
            prov = secrets.setdefault(provider, {})
            prov["key"] = api_key
            self._save(data)

    def get_secret(self, provider: str) -> str | None:
        try:
            import keyring  # type: ignore

            val = keyring.get_password(
                "hippocampus", f"{provider}.api_key:{self.scope}"
            )
            if val:
                return val
        except Exception:
            pass
        data = self._load()
        return (
            data.get("secrets", {}).get(provider, {}).get("key")
            if isinstance(data, dict)
            else None
        )

    def apply_yaml(self, yaml_path: str, reset: bool = False) -> None:
        import yaml  # lazy import

        p = Path(yaml_path).expanduser().resolve()
        content = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not isinstance(content, dict):
            raise ValueError("YAML root must be a mapping")

        data = {} if reset else dict(self._load())

        # secrets: api.*.key
        self._apply_yaml_secrets(content)
        # validate engine/api sections (non-secret fields after stripping)
        stripped = self._strip_secret_keys(content)
        self._validate_engine_section(stripped.get("engine"))
        self._validate_api_section(stripped.get("api"))
        # merge the rest
        merged = self._merge_dicts(data, stripped)
        self._save(merged)

    def _validate_engine_section(self, engine_section: Any) -> None:
        if not isinstance(engine_section, dict):
            return
        for k in engine_section.keys():
            if k not in _SUPPORTED_ENGINE_KEYS:
                raise ValueError(
                    f"unsupported engine key '{k}'; allowed: "
                    + ", ".join(sorted(_SUPPORTED_ENGINE_KEYS))
                )
        prov = engine_section.get("provider")
        if prov is not None and prov not in _SUPPORTED_PROVIDERS:
            raise ValueError(
                "unsupported provider; allowed: "
                + ", ".join(sorted(_SUPPORTED_PROVIDERS))
            )

    def _validate_api_section(self, api_section: Any) -> None:
        if not isinstance(api_section, dict):
            return
        for prov, conf in api_section.items():
            if prov not in _SUPPORTED_PROVIDERS:
                raise ValueError(
                    "unsupported API provider; allowed: "
                    + ", ".join(sorted(_SUPPORTED_PROVIDERS))
                )
            if not isinstance(conf, dict):
                raise ValueError("api.<provider> must be a mapping")

    def _apply_yaml_secrets(self, content: Dict[str, Any]) -> None:
        api = content.get("api", {}) if isinstance(content.get("api", {}), dict) else {}
        for provider, conf in api.items():
            if isinstance(conf, dict):
                key = conf.get("key")
                if key:
                    self.set_secret(provider, str(key))

    def _strip_secret_keys(self, content: Dict[str, Any]) -> Dict[str, Any]:
        def strip_api(d: Dict[str, Any]) -> Dict[str, Any]:
            out: Dict[str, Any] = {}
            for prov, pval in d.items():
                if isinstance(pval, dict):
                    cp = {k: v for k, v in pval.items() if k != "key"}
                    if cp:
                        out[prov] = cp
            return out

        res: Dict[str, Any] = {}
        for k, v in content.items():
            if k == "api" and isinstance(v, dict):
                res["api"] = strip_api(v)
            else:
                res[k] = v
        return res

    def _merge_dicts(
        self, base: Dict[str, Any], incoming: Dict[str, Any]
    ) -> Dict[str, Any]:
        def merge(dst: Dict[str, Any], src: Dict[str, Any]) -> None:
            for k, v in src.items():
                if isinstance(v, dict) and isinstance(dst.get(k), dict):
                    merge(dst[k], v)  # type: ignore[index]
                else:
                    dst[k] = v

        out = dict(base)
        merge(out, incoming)
        return out
