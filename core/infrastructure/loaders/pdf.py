"""Infrastructure loader for PDF files using `pypdf`.

Assumes `pypdf` is available at runtime. Text extraction is simplistic and
intended for heuristic reference discovery, not layout preservation.
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
        from pypdf import PdfReader  # type: ignore

        p = Path(file_path).expanduser().resolve()
        reader = PdfReader(str(p))
        chunks: list[str] = []
        for page in reader.pages:
            try:
                chunks.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001
                continue
        return "\n".join(
            line.rstrip() for line in "\n".join(chunks).splitlines()
        ).strip()
