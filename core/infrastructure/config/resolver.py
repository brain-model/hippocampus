from __future__ import annotations

from typing import Any

from .manager import ConfigManager


def resolve_engine_config(
    overrides: dict[str, Any] | None = None,
    scopes: tuple[str, ...] = ("local", "global"),
) -> tuple[dict[str, Any], dict[str, str]]:
    """Resolve engine configuration with precedence and provenance.

    Precedence: CLI overrides > local > global. Applies a default for provider
    when absent ("openai"). Returns merged config and a provenance map per key.
    """
    merged: dict[str, Any] = {}
    provenance: dict[str, str] = {}

    # Merge strategy: first-write-wins entre escopos de config
    # Ordem de merge: local -> global (valores já definidos não são sobrescritos)
    # Overrides (CLI) são aplicados POR ÚLTIMO e SEMPRE sobrescrevem
    _merge_scope(merged, provenance, scopes, "local")
    _merge_scope(merged, provenance, scopes, "global")

    if overrides:
        _apply_overrides(merged, provenance, overrides)

    if "provider" not in merged:
        merged["provider"] = "openai"
        provenance["provider"] = "default"

    return merged, provenance


def _merge_scope(
    merged: dict[str, Any],
    provenance: dict[str, str],
    scopes: tuple[str, ...],
    scope: str,
) -> None:
    if scope not in scopes:
        return
    eng = ConfigManager(scope).get("engine", {}) or {}
    if not isinstance(eng, dict):
        return
    for k, v in eng.items():
        if v is None or k in merged:
            continue
        merged[k] = v
        provenance[k] = scope


def _apply_overrides(
    merged: dict[str, Any], provenance: dict[str, str], overrides: dict[str, Any]
) -> None:
    for k, v in overrides.items():
        if v is None:
            continue
        merged[k] = v
        provenance[k] = "cli"
