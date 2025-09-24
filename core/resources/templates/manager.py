"""Templates manager: render helpers for CLI and outputs.

This module provides the `render_template` function used across the CLI to
render small text templates stored alongside this package using Jinja2.
Keeping the implementation here allows `__init__.py` to remain import-only.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

_TEMPLATES_DIR = Path(__file__).parent

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=False,  # nosec B701 - Templates generate YAML/JSON, not HTML
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_template(name: str, **kwargs) -> str:
    """Render a text template from this package using Jinja2.

    Args:
        name: Template filename (e.g., ``config_set.j2``).
        **kwargs: Placeholder values for substitution.

    Returns:
        The rendered string.
    """
    template = _env.get_template(name)
    return template.render(**kwargs)
