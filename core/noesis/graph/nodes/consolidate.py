from __future__ import annotations

import time
from typing import Any


def run(_classifications, extractions) -> dict[str, Any]:
    start = time.time()
    refs = extractions.get("extractions", []) if isinstance(extractions, dict) else []
    metrics = {
        "latency_ms": int((time.time() - start) * 1000),
        "tokens": {"prompt": 0, "completion": 0},
        "node": "consolidate",
    }
    return {"references": refs, "metrics": metrics}
