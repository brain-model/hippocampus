from __future__ import annotations

import re
import time

from ..types import NodeResult


URL_RE = re.compile(r"https?://[^\s)\]\}\>]+", re.IGNORECASE)
TRAILING_PUNCT = ",.;:)]}\'\">"


def run(text: str) -> NodeResult:
    start = time.time()
    classifications = []
    for m in URL_RE.finditer(text or ""):
        span = m.group(0).rstrip(TRAILING_PUNCT)
        classifications.append({
            "kind": "web_link",
            "confidence": 0.9,
            "span": span,
        })
    metrics = {
        "latency_ms": int((time.time() - start) * 1000),
        "tokens": {"prompt": 0, "completion": 0},
        "node": "classify",
    }
    return {"classifications": classifications, "metrics": metrics}
