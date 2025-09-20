from __future__ import annotations

from core.resources.templates import render_template


def test_render_template_config_set_ok():
    msg = render_template(
        "config_set.j2", scope="local", key="engine.model", value="gpt-4o-mini"
    )
    assert "local set: engine.model=gpt-4o-mini" in msg
