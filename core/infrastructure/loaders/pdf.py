"""Infrastructure loader for PDF files using `pypdf`.

This loader requires `pypdf` to be available. The project ships as a full
install, então `pypdf` deve estar presente nas instalações padrão. Se faltar,
o ambiente está inconsistente: reinstale o pacote ou rode `uv sync`.

Text extraction is simplistic and intended for heuristic reference discovery,
not layout preservation.
"""

from __future__ import annotations

from pathlib import Path


class PdfLoader:
    """PDF loader based on `pypdf`. Assumes dependency is available."""

    def load(self, *, text: str | None = None, file_path: str | None = None) -> str:
        if text is not None:
            return text
        if file_path is None:
            raise ValueError("Provide file_path for PDF loading")
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "Dependência obrigatória ausente: pypdf. Reinstale o pacote ou "
                "execute 'uv sync' para corrigir o ambiente."
            ) from e

        p = Path(file_path).expanduser().resolve()
        reader = PdfReader(str(p))
        chunks: list[str] = []
        for page in reader.pages:
            try:
                chunks.append(page.extract_text() or "")
            except Exception:  # pragma: no cover
                chunks.append("")
        return "\n".join(
            line.rstrip() for line in "\n".join(chunks).splitlines()
        ).strip()
