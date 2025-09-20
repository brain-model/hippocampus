"""Templates package public API.

This module should not contain implementations, only re-exports. The
rendering implementation lives in ``templates.manager``.
"""

from .manager import render_template

__all__ = [
    "render_template",
]
