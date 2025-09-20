from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.infrastructure.config.manager import ConfigManager


# === HAPPY PATH TESTS ===
def test_manager_basic_get_set(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mgr = ConfigManager("local")
    mgr.set("engine.provider", "openai")
    assert mgr.get("engine.provider") == "openai"
    assert mgr.get("engine.model", "default") == "default"


def test_manager_apply_yaml_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = Path("valid.yaml")
    p.write_text("""
engine:
  provider: openai
  model: gpt-4o-mini
api:
  openai:
    key: sk-test
    """.strip(), encoding="utf-8")
    mgr = ConfigManager("local")
    mgr.apply_yaml(str(p))
    assert mgr.get("engine.provider") == "openai"
    assert mgr.get("engine.model") == "gpt-4o-mini"


def test_manager_secret_operations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    class DummyKeyring:
        def __init__(self):
            self.store = {}

        def set_password(self, service, username, password):
            self.store[f"{service}:{username}"] = password

        def get_password(self, service, username):
            return self.store.get(f"{service}:{username}")

    keyring = DummyKeyring()
    monkeypatch.setitem(__import__("sys").modules, "keyring", keyring)
    mgr = ConfigManager("local")
    mgr.set_secret("openai", "sk-test")
    assert mgr.get_secret("openai") == "sk-test"


# === ERROR TESTS ===
def test_set_api_key_direct_should_fail(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mgr = ConfigManager("local")
    # api.openai sem .key deve falhar
    with pytest.raises(ValueError):
        mgr.set("api.openai", "sk-xxx")
    with pytest.raises(ValueError):
        mgr.set("api.openai", {"key": "sk-xxx"})


def test_apply_yaml_invalid_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mgr = ConfigManager("local")
    p = Path("bad.yaml")
    p.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mgr.apply_yaml(str(p))


def test_apply_yaml_invalid_engine_and_api(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mgr = ConfigManager("local")
    p = Path("bad2.yaml")
    p.write_text(json.dumps({
        "engine": {"unsupported": 1, "provider": "nope"},
        "api": {"badprov": {"extra": 1}}
    }), encoding="utf-8")
    with pytest.raises(ValueError):
        mgr.apply_yaml(str(p))


def test_set_invalid_engine_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mgr = ConfigManager("local")
    with pytest.raises(ValueError):
        mgr.set("engine.unsupported", 1)
    with pytest.raises(ValueError):
        mgr.set("engine.provider", "nope")


def test_load_invalid_json_defaults_to_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg_path = tmp_path / ".hippo" / "config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("{invalid json}", encoding="utf-8")
    mgr = ConfigManager("local")
    # .get deve retornar default quando JSON está inválido
    assert mgr.get("engine.provider", "missing") == "missing"


def test_set_secret_keyring_fallback(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # injeta um módulo keyring que sempre falha

    class BadKeyring:
        def set_password(self, *_args, **_kwargs):
            raise RuntimeError("no keyring")

        def get_password(self, *_args, **_kwargs):
            raise RuntimeError("no keyring")

    monkeypatch.setitem(__import__("sys").modules, "keyring", BadKeyring())
    mgr = ConfigManager("local")
    mgr.set_secret("openai", "sk-fallback")
    # deve recuperar do fallback em arquivo
    assert mgr.get_secret("openai") == "sk-fallback"


def test_engine_key_validation_in_set(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mgr = ConfigManager("local")
    # chave inválida
    with pytest.raises(ValueError):
        mgr.set("engine.unknown", 1)
    # provider inválido
    with pytest.raises(ValueError):
        mgr.set("engine.provider", "nope")


def test_merge_nested_dicts_on_apply(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mgr = ConfigManager("local")
    mgr.set("engine.provider", "openai")
    p = Path("merge.yaml")
    p.write_text("""
engine:
  model: gpt-4o-mini
    """.strip(), encoding="utf-8")
    mgr.apply_yaml(str(p))
    # deve preservar provider e adicionar model
    assert mgr.get("engine.provider") == "openai"
    assert mgr.get("engine.model") == "gpt-4o-mini"
