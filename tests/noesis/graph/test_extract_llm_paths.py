from __future__ import annotations

import sys
import types
import pytest

from core.noesis.graph.nodes import extract as node_extract
from core.noesis.graph.types import GraphConfig


class _FakeAgentOK:
    last_cfg_override = None

    def __init__(self, cfg_override=None):
        _FakeAgentOK.last_cfg_override = cfg_override or {}
        self.last_tokens = {"prompt": 3, "completion": 5}
        self.last_extract_latency_ms = 42

    def extract(self, text: str):
        return {
            "references": [
                {
                    "id": 1,
                    "referenceType": "web_link",
                    "rawString": "http://x",
                    "sourceFormat": "web_content",
                    "sourcePath": "http://x",
                    "details": {},
                }
            ]
        }


class _FakeAgentRaises:
    def __init__(self, cfg_override=None):  # noqa: ARG002
        raise RuntimeError("boom")


def _install_fake_agent(monkeypatch, cls):
    fake_mod = types.ModuleType("core.infrastructure.extraction.langchain_agent")
    fake_mod.LangChainExtractionAgent = cls
    monkeypatch.setitem(sys.modules, "core.infrastructure.extraction.langchain_agent", fake_mod)

    fake_resolver = types.ModuleType("core.infrastructure.config.resolver")

    def _fake_resolve_engine_config(_overrides):  # noqa: ARG001
        return {}, {}

    fake_resolver.resolve_engine_config = _fake_resolve_engine_config
    monkeypatch.setitem(sys.modules, "core.infrastructure.config.resolver", fake_resolver)


class _FakeAgentRetryThenOK:
    calls = 0

    def __init__(self, cfg_override=None):  # noqa: ARG002
        pass

    def extract(self, text: str):  # noqa: ARG002
        _FakeAgentRetryThenOK.calls += 1
        if _FakeAgentRetryThenOK.calls < 2:
            raise RuntimeError("transient")
        return {
            "references": [
                {
                    "id": 1,
                    "referenceType": "web_link",
                    "rawString": "http://y",
                    "sourceFormat": "web_content",
                    "sourcePath": "http://y",
                    "details": {},
                }
            ]
        }


class _FakeAgentAlwaysTimeout:
    def __init__(self, cfg_override=None):  # noqa: ARG002
        pass

    def extract(self, text: str):  # noqa: ARG002
        raise TimeoutError("deadline")


def test_extract_llm_success_uses_tokens_latency_and_overlays_cfg(monkeypatch):
    _install_fake_agent(monkeypatch, _FakeAgentOK)
    cfg = GraphConfig(enabled=True, timeout_s=7, retries=2)
    prev = {"classifications": []}
    out = node_extract.run("see http://x", prev, cfg)
    assert isinstance(out, dict)
    ex = out.get("extractions")
    assert isinstance(ex, list) and len(ex) == 1
    m = out.get("metrics")
    assert m["latency_ms"] == 42
    assert m["tokens"] == {"prompt": 3, "completion": 5}
    # cfg overlay aplicado
    assert _FakeAgentOK.last_cfg_override.get("timeout_s") == 7
    assert _FakeAgentOK.last_cfg_override.get("retries") == 2


def test_extract_llm_exception_with_fallback_true(monkeypatch):
    _install_fake_agent(monkeypatch, _FakeAgentRaises)
    cfg = GraphConfig(enabled=True, use_fallback=True)
    prev = {"classifications": []}
    out = node_extract.run("see http://x", prev, cfg)
    ex = out.get("extractions")
    assert isinstance(ex, list) and len(ex) >= 1  # heurística capturou URL
    m = out.get("metrics")
    assert isinstance(m.get("latency_ms"), int) and m["latency_ms"] >= 0
    assert m.get("tokens") == {"prompt": 0, "completion": 0}


def test_extract_llm_exception_without_fallback_returns_empty(monkeypatch):
    _install_fake_agent(monkeypatch, _FakeAgentRaises)
    cfg = GraphConfig(enabled=True, use_fallback=False)
    prev = {"classifications": []}
    out = node_extract.run("see http://x", prev, cfg)
    assert out.get("extractions") == []
    m = out.get("metrics")
    assert isinstance(m.get("latency_ms"), int) and m["latency_ms"] >= 0
    assert m.get("tokens") == {"prompt": 0, "completion": 0}


def test_extract_llm_retries_and_succeeds(monkeypatch):
    _install_fake_agent(monkeypatch, _FakeAgentRetryThenOK)
    _FakeAgentRetryThenOK.calls = 0
    cfg = GraphConfig(enabled=True, retries=2)
    prev = {"classifications": []}
    out = node_extract.run("see http://y", prev, cfg)
    ex = out.get("extractions")
    assert isinstance(ex, list) and len(ex) == 1


def test_extract_llm_timeout_with_fallback(monkeypatch):
    _install_fake_agent(monkeypatch, _FakeAgentAlwaysTimeout)
    cfg = GraphConfig(enabled=True, use_fallback=True, retries=1)
    prev = {"classifications": []}
    out = node_extract.run("see http://y", prev, cfg)
    ex = out.get("extractions")
    assert isinstance(ex, list) and len(ex) >= 1


def test_extract_llm_timeout_without_fallback_raises(monkeypatch):
    _install_fake_agent(monkeypatch, _FakeAgentAlwaysTimeout)
    cfg = GraphConfig(enabled=True, use_fallback=False, retries=1)
    prev = {"classifications": []}
    with pytest.raises(TimeoutError):
        node_extract.run("see http://y", prev, cfg)
