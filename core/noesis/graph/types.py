from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict


class Classification(TypedDict, total=False):
    kind: str  # e.g., 'web_link' | 'in_text_citation' | 'other'
    confidence: float
    span: Optional[str]


class Extraction(TypedDict, total=False):
    referenceType: str
    rawString: str
    sourceFormat: str
    sourcePath: str
    details: Dict[str, Any]


class Metrics(TypedDict, total=False):
    latency_ms: int
    tokens: Dict[str, int]
    node: str


class NodeResult(TypedDict, total=False):
    classifications: List[Classification]
    extractions: List[Extraction]
    metrics: Metrics
    llm: Dict[str, str]


@dataclass
class GraphConfig:
    enabled: bool = False
    use_fallback: bool = True
    timeout_s: int = 60
    retries: int = 0
    engine_overrides: Optional[Dict[str, Any]] = None
    backoff_base_s: float = 0.1
    backoff_max_s: float = 2.0
    jitter_s: float = 0.05
