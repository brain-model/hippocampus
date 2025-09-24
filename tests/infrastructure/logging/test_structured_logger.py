from __future__ import annotations

import json
from pathlib import Path

from core.infrastructure.logging.structured import get_logger


def test_structured_logger_writes_json_and_masks(tmp_path: Path):
    log_path = tmp_path / "app.log"
    logger = get_logger(
        name="test.logger",
        level="DEBUG",
        console_output=False,
        file_output=str(log_path),
        json_format=True,
        mask_secrets=True,
    )

    # Message and extras containing secrets should be masked
    logger.info(
        "Connecting with api_key=XYZ123 and token=abc",
        api_key="XYZ123",
        token="abc",
        nested_secret="should_hide",
        normal_field="ok",
    )
    logger.debug("Debug message")
    logger.warning("Warn message")
    logger.error("Error message")
    logger.critical("Critical message")

    data = [
        json.loads(line) for line in log_path.read_text().splitlines() if line.strip()
    ]
    assert len(data) >= 5

    first = data[0]
    # Basic JSON structure
    assert first["name"] == "test.logger"
    assert first["level"] in {"INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"}
    assert isinstance(first["timestamp"], str)

    # Masking behavior
    # Message text should have secrets masked
    assert 'api_key="***"' in first["message"] or "api_key=***" in first["message"]
    assert 'token="***"' in first["message"] or "token=***" in first["message"]

    # Extra fields with secret-like keys should be masked
    assert first.get("api_key") == "***"
    assert first.get("token") == "***"
    # Non-secret field should remain
    assert first.get("normal_field") == "ok"


def test_get_logger_accepts_str_path(tmp_path: Path):
    log_path = tmp_path / "strpath.log"
    logger = get_logger(
        name="test.logger2",
        level="INFO",
        console_output=False,
        file_output=str(log_path),
        json_format=True,
    )
    logger.info("Hello", some_field="value")
    lines = [
        json.loads(line) for line in log_path.read_text().splitlines() if line.strip()
    ]
    assert lines and lines[0]["some_field"] == "value"
