"""Structured logging system for hippocampus with rich integration.

This module provides a configurable logging infrastructure that supports:
- Console output with rich formatting
- File output with structured JSON
- Debug mode with detailed traces
- Automatic secret masking for security
"""

import json
import logging
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler


class StructuredLogger:
    """Structured logger with rich console integration and secret masking."""

    def __init__(
        self,
        name: str,
        level: str = "INFO",
        console_output: bool = True,
        file_output: Path | None = None,
        json_format: bool = False,
        mask_secrets: bool = True,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name (typically module name)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Enable rich console output
            file_output: Optional file path for logging
            json_format: Use JSON format for file output
            mask_secrets: Automatically mask API keys and secrets
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.console_output = console_output
        self.file_output = file_output
        self.json_format = json_format
        self.mask_secrets = mask_secrets

        # Rich console for formatted output
        self.console = Console(stderr=True)

        # Configure logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Add console handler with rich formatting
        if console_output:
            console_handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=False,
                rich_tracebacks=True,
            )
            console_handler.setLevel(self.level)
            self.logger.addHandler(console_handler)

        # Add file handler if specified
        if file_output:
            file_handler = logging.FileHandler(file_output)
            file_handler.setLevel(logging.DEBUG)  # File gets all levels

            if json_format:
                formatter = JsonFormatter(mask_secrets=mask_secrets)
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )

            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _mask_message(self, message: str, extra: dict[str, Any] | None = None) -> str:
        """Mask secrets in log messages."""
        if not self.mask_secrets:
            return message

        # Common secret patterns to mask
        secret_patterns = [
            "api_key",
            "apikey",
            "api-key",
            "token",
            "secret",
            "password",
            "pwd",
            "auth",
            "authorization",
        ]

        masked_message = message

        # Mask in message text
        for pattern in secret_patterns:
            if pattern in masked_message.lower():
                # Replace potential secret values (simple heuristic)
                import re

                masked_message = re.sub(
                    rf'{pattern}["\s]*[:=]["\s]*[^"\s,}}]+',
                    f'{pattern}="***"',
                    masked_message,
                    flags=re.IGNORECASE,
                )

        # Mask in extra data if provided
        if extra:
            for key, _value in extra.items():
                if any(pattern in key.lower() for pattern in secret_patterns):
                    extra[key] = "***"

        return masked_message

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        message = self._mask_message(message, kwargs)
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        message = self._mask_message(message, kwargs)
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        message = self._mask_message(message, kwargs)
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        message = self._mask_message(message, kwargs)
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        message = self._mask_message(message, kwargs)
        self.logger.critical(message, extra=kwargs)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured file logging."""

    def __init__(self, mask_secrets: bool = True):
        super().__init__()
        self.mask_secrets = mask_secrets

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in log_data and not key.startswith("_"):
                    # Mask secrets in extra data
                    if self.mask_secrets and any(
                        secret in key.lower()
                        for secret in ["key", "token", "secret", "password", "auth"]
                    ):
                        log_data[key] = "***"
                    else:
                        log_data[key] = value

        return json.dumps(log_data, default=str)


def get_logger(
    name: str,
    level: str = "INFO",
    console_output: bool = True,
    file_output: str | Path | None = None,
    json_format: bool = False,
    mask_secrets: bool = True,
) -> StructuredLogger:
    """Get or create a structured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable rich console output
        file_output: Optional file path for logging
        json_format: Use JSON format for file output
        mask_secrets: Automatically mask API keys and secrets

    Returns:
        Configured StructuredLogger instance
    """
    if isinstance(file_output, str):
        file_output = Path(file_output)

    return StructuredLogger(
        name=name,
        level=level,
        console_output=console_output,
        file_output=file_output,
        json_format=json_format,
        mask_secrets=mask_secrets,
    )
