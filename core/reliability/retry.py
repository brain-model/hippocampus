from __future__ import annotations

import random
import time
from typing import Any, Callable, Dict, Tuple

# Defaults centralizados para backoff
DEFAULT_BACKOFF_BASE_S = 0.1
DEFAULT_BACKOFF_MAX_S = 2.0
DEFAULT_JITTER_S = 0.05


def _extract_status_code(err: Exception) -> int | None:
    # Tenta obter status de atributos comuns
    code = getattr(err, "status_code", None)
    if isinstance(code, int):
        return code
    resp = getattr(err, "response", None)
    if resp is not None:
        sc = getattr(resp, "status_code", None)
        if isinstance(sc, int):
            return sc
    # Alguns SDKs usam .code como número
    c = getattr(err, "code", None)
    if isinstance(c, int):
        return c
    return None


def is_transient_error(err: Exception) -> bool:
    name = type(err).__name__
    msg = str(err).lower()
    status = _extract_status_code(err)
    if status is not None:
        if status == 429:
            return True
        if 500 <= status < 600:
            return True
    if isinstance(err, TimeoutError):
        return True
    transient_names = {
        "RateLimitError",
        "RateLimit",
        "ResourceExhausted",
        "DeadlineExceeded",
        "ServiceUnavailable",
        "InternalServerError",
        "Unavailable",
    }
    if name in transient_names:
        return True
    if (
        "rate limit" in msg
        or "quota" in msg
        or "exceeded" in msg
        or "unavailable" in msg
        or "network" in msg
        or "connection" in msg
        or "temporar" in msg  # temporary/temporarily
        or "reset by peer" in msg
    ):
        return True
    return False


def is_permanent_error(err: Exception) -> bool:
    name = type(err).__name__
    msg = str(err).lower()
    status = _extract_status_code(err)
    if status is not None and status in (400, 401, 403, 404):
        return True
    permanent_names = {
        "AuthenticationError",
        "AuthError",
        "PermissionDenied",
        "InvalidRequestError",
        "ValueError",
        "ImportError",
    }
    if name in permanent_names:
        return True
    if "missing api key" in msg or "invalid api key" in msg or "permission denied" in msg:
        return True
    return False


def compute_backoff_seconds(
    base_s: float, jitter_s: float, max_s: float, attempt_index: int
) -> float:
    return min((base_s * (2 ** attempt_index)) + random.uniform(0, jitter_s), max_s)


def retry_call(
    func: Callable[[], Tuple[Any, Dict[str, int] | None, int | None, Dict[str, str] | None] | Any],
    attempts: int,
    base_s: float,
    jitter_s: float,
    max_s: float,
    should_retry: Callable[[Exception], bool],
):
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return func()
        except Exception as e:  # noqa: BLE001
            last_err = e
            if i < attempts - 1 and should_retry(e):
                time.sleep(compute_backoff_seconds(base_s, jitter_s, max_s, i))
                continue
            break
    assert last_err is not None
    raise last_err
