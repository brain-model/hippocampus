from __future__ import annotations

import pytest

from core.infrastructure.config.manager import ConfigManager
from core.infrastructure.config.resolver import resolve_engine_config


def test_resolver_precedence_cli_over_local_over_global(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    # prepare global
    g = ConfigManager("global")
    g.set("engine.model", "gpt-4o-mini")
    g.set("engine.temperature", 0.1)
    # prepare local
    local_mgr = ConfigManager("local")
    local_mgr.set("engine.temperature", 0.2)
    local_mgr.set("engine.max_tokens", 64)

    merged, prov = resolve_engine_config(
        overrides={"temperature": 0.3, "timeout_s": 30}, scopes=("local", "global")
    )
    assert merged["model"] == "gpt-4o-mini"
    assert prov["model"] == "global"
    assert merged["max_tokens"] == 64 and prov["max_tokens"] == "local"
    assert merged["temperature"] == pytest.approx(0.3) and prov["temperature"] == "cli"
    assert merged["timeout_s"] == 30 and prov["timeout_s"] == "cli"
    assert merged["provider"] == "openai" and prov["provider"] == "default"


def test_resolver_scopes_subset_only_local(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    local_mgr = ConfigManager("local")
    local_mgr.set("engine.model", "gemini-1.5-flash")
    merged, prov = resolve_engine_config(scopes=("local",))
    assert merged["model"] == "gemini-1.5-flash"
    assert prov["model"] == "local"


def test_resolver_ignores_none_and_non_dict(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Write None values; resolver should ignore them
    local_mgr = ConfigManager("local")
    local_mgr.set("engine.model", None)  # type: ignore[arg-type]
    local_mgr.set("engine.temperature", None)  # type: ignore[arg-type]
    merged, prov = resolve_engine_config()
    # provider default kicks in, nothing else
    assert merged["provider"] == "openai"
    # Pode ser "default" ou "global" dependendo se há config global
    assert prov["provider"] in ("default", "global")


def test_resolver_empty_scopes_and_none_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Nenhum escopo
    merged, prov = resolve_engine_config(scopes=())
    assert merged["provider"] == "openai" and prov["provider"] == "default"
    # Escopo local sem engine
    mgr = ConfigManager("local")
    merged2, prov2 = resolve_engine_config(scopes=("local",))
    assert merged2["provider"] == "openai" and prov2["provider"] == "default"
    # Engine com valores None
    mgr.set("engine.model", None)
    mgr.set("engine.temperature", None)
    merged3, _ = resolve_engine_config(scopes=("local",))
    assert merged3["provider"] == "openai"
    # Overrides com None
    merged4, _ = resolve_engine_config(overrides={"model": None, "timeout_s": None})
    assert merged4["provider"] == "openai"


def test_resolver_overrides_behavior(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    g = ConfigManager("global")
    g.set("engine.model", "gpt-4o-mini")
    g.set("engine.temperature", 0.1)
    local_config = ConfigManager("local")
    local_config.set("engine.temperature", 0.2)
    local_config.set("engine.max_tokens", 64)
    merged, prov = resolve_engine_config(
        overrides={"temperature": 0.3, "timeout_s": 30}, scopes=("local", "global")
    )
    assert merged["model"] == "gpt-4o-mini"
    assert prov["model"] == "global"
    assert merged["max_tokens"] == 64 and prov["max_tokens"] == "local"
    assert merged["temperature"] == pytest.approx(0.3) and prov["temperature"] == "cli"
    assert merged["timeout_s"] == 30 and prov["timeout_s"] == "cli"
    # Provider pode ser "default" ou "global" dependendo se há config global
    assert merged["provider"] == "openai" and prov["provider"] in ("default", "global")
