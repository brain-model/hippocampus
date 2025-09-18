"""Heuristic extraction utilities for references and citations.

Detects URLs and basic in-text citations from normalized text inputs,
producing manifest-compatible reference entries.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

URL_RE = re.compile(r"https?://\S+")
CITATION_RE = re.compile(r"([A-Z][A-Za-z\-]+)\s*\((\d{4})\)")


class HeuristicExtractionAgent:
    """Heuristic reference extractor.

    Detects URLs and in-text citations in the form "Author (YYYY)" and
    generates reference entries compatible with the manifest schema.
    """

    def extract(self, text: str) -> Dict[str, Any]:
        """Extract references from normalized text.

        Args:
            text: Normalized text for heuristic analysis.

        Returns:
            A dictionary with key `references` containing the detected
            references (URLs and in-text citations).
        """
        references: List[Dict[str, Any]] = []

        for idx, url in enumerate(URL_RE.findall(text), start=1):
            references.append(
                {
                    "id": idx,
                    "rawString": url,
                    "referenceType": "web_link",
                    "sourceFormat": "web_content",
                    "sourcePath": url,
                    "details": {},
                }
            )

        base = len(references)
        for jdx, m in enumerate(CITATION_RE.finditer(text), start=1):
            author, year = m.group(1), m.group(2)
            references.append(
                {
                    "id": base + jdx,
                    "rawString": m.group(0),
                    "referenceType": "in_text_citation",
                    "sourceFormat": "text",
                    "sourcePath": "",
                    "details": {"author": author, "year": int(year)},
                }
            )

        return {"references": references}
