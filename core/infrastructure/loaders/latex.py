"""Infrastructure loader for LaTeX files with basic cleanup.

Removes common LaTeX commands/environments and returns readable text,
preserving URLs where possible. This is a lightweight approximation to
facilitate heuristic extraction without external dependencies.
"""

from __future__ import annotations

import re
from pathlib import Path


class LatexLoader:
    """Simple LaTeX loader that strips commands and normalizes text.

    It preserves the contents of braced arguments for common commands, e.g.:
    - ``\\section{Intro}`` → ``Intro``
    - ``\\textbf{bold}`` → ``bold``
    - ``\\url{https://ex.com}`` → ``https://ex.com``
    """

    # Remove full environments like figures, tables, etc.
    ENV_RE = re.compile(r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}", re.DOTALL)
    # Extract URL content
    URL_RE = re.compile(r"\\url\{([^}]+)\}")
    # Replace commands with a single braced argument with that argument's text
    CMD_WITH_ARG_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}")
    # Remove remaining commands (without braced args)
    BARE_CMD_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?")

    def load(self, *, text: str | None = None, file_path: str | None = None) -> str:
        if text is None and file_path is None:
            raise ValueError("Provide either text or file_path")
        if text is not None and file_path is not None:
            raise ValueError("Provide only one of text or file_path")
        if text is None:
            p = Path(file_path).expanduser().resolve()
            text = p.read_text(encoding="utf-8", errors="ignore")

        s = self.ENV_RE.sub(" ", text)
        s = self.URL_RE.sub(r"\1", s)
        s = self.CMD_WITH_ARG_RE.sub(r"\1", s)
        s = self.BARE_CMD_RE.sub(" ", s)
        return "\n".join(line.rstrip() for line in s.splitlines()).strip()
