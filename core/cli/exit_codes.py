"""Exit codes for hippocampus CLI.

Standard exit codes to provide consistent error reporting
and enable better automation/scripting.
"""

from enum import IntEnum


class ExitCode(IntEnum):
    """Standard exit codes for hippocampus CLI."""

    # Success
    SUCCESS = 0

    # General errors (1-10)
    GENERAL_ERROR = 1
    INVALID_ARGUMENT = 2
    FILE_NOT_FOUND = 3
    PERMISSION_ERROR = 4
    CONFIG_ERROR = 5

    # LLM/Provider errors (11-20)
    LLM_ERROR = 11
    API_KEY_MISSING = 12
    API_QUOTA_EXCEEDED = 13
    API_TIMEOUT = 14
    API_AUTHENTICATION_ERROR = 15
    API_RATE_LIMITED = 16

    # Validation errors (21-30)
    SCHEMA_VALIDATION_ERROR = 21
    MANIFEST_VERSION_ERROR = 22
    INVALID_JSON = 23

    # Processing errors (31-40)
    PROCESSING_ERROR = 31
    EXTRACTION_ERROR = 32
    LOADER_ERROR = 33
    FORMATTER_ERROR = 34

    # System errors (41-50)
    SYSTEM_ERROR = 41
    DEPENDENCY_ERROR = 42
    DISK_FULL = 43
    MEMORY_ERROR = 44


def get_exit_code_for_exception(exception: Exception) -> ExitCode:
    """Map exception types to appropriate exit codes.

    Args:
        exception: The exception that occurred

    Returns:
        Appropriate exit code based on exception type
    """
    exception_type = type(exception).__name__
    exception_str = str(exception).lower()

    # Try different error categories in order of specificity
    return (
        _get_filesystem_error_code(exception_type)
        or _get_memory_error_code(exception_type)
        or _get_validation_error_code(exception_type)
        or _get_api_error_code(exception_type, exception_str)
        or _get_processing_error_code(exception_type)
        or _get_dependency_error_code(exception_type)
        or _get_config_error_code(exception_type, exception_str)
        or ExitCode.GENERAL_ERROR
    )


def _get_filesystem_error_code(exception_type: str) -> ExitCode | None:
    """Get exit code for filesystem-related errors."""
    if exception_type == "FileNotFoundError":
        return ExitCode.FILE_NOT_FOUND
    if exception_type == "PermissionError":
        return ExitCode.PERMISSION_ERROR
    if exception_type in ["OSError", "IOError"]:
        return ExitCode.SYSTEM_ERROR
    return None


def _get_memory_error_code(exception_type: str) -> ExitCode | None:
    """Get exit code for memory-related errors."""
    if exception_type == "MemoryError":
        return ExitCode.MEMORY_ERROR
    return None


def _get_validation_error_code(exception_type: str) -> ExitCode | None:
    """Get exit code for validation-related errors."""
    if exception_type in ["JSONDecodeError", "json.JSONDecodeError"]:
        return ExitCode.INVALID_JSON
    if exception_type in ["ValidationError", "SchemaValidationError"]:
        return ExitCode.SCHEMA_VALIDATION_ERROR
    if exception_type == "ManifestVersionError":
        return ExitCode.MANIFEST_VERSION_ERROR
    return None


def _get_api_error_code(exception_type: str, exception_str: str) -> ExitCode | None:
    """Get exit code for API-related errors."""
    if _is_timeout_error(exception_type, exception_str):
        return ExitCode.API_TIMEOUT
    if _is_auth_error(exception_str):
        return ExitCode.API_AUTHENTICATION_ERROR
    if _is_rate_limit_error(exception_str):
        return ExitCode.API_RATE_LIMITED
    if _is_quota_error(exception_str):
        return ExitCode.API_QUOTA_EXCEEDED
    if _is_llm_provider_error(exception_type):
        return ExitCode.LLM_ERROR
    return None


def _get_processing_error_code(exception_type: str) -> ExitCode | None:
    """Get exit code for processing-related errors."""
    if _is_extraction_error(exception_type):
        return ExitCode.EXTRACTION_ERROR
    if _is_loader_error(exception_type):
        return ExitCode.LOADER_ERROR
    if _is_formatter_error(exception_type):
        return ExitCode.FORMATTER_ERROR
    return None


def _get_dependency_error_code(exception_type: str) -> ExitCode | None:
    """Get exit code for dependency-related errors."""
    if exception_type in ["ImportError", "ModuleNotFoundError"]:
        return ExitCode.DEPENDENCY_ERROR
    return None


def _get_config_error_code(exception_type: str, exception_str: str) -> ExitCode | None:
    """Get exit code for configuration-related errors."""
    if _is_config_error(exception_type, exception_str):
        return ExitCode.CONFIG_ERROR
    return None


def _is_timeout_error(exception_type: str, exception_str: str) -> bool:
    """Check if exception is a timeout error."""
    return (
        "timeout" in exception_type.lower()
        or "TimeoutError" in exception_type
        or "timeout" in exception_str
    )


def _is_auth_error(exception_str: str) -> bool:
    """Check if exception is an authentication error."""
    return "authentication" in exception_str or "auth" in exception_str


def _is_rate_limit_error(exception_str: str) -> bool:
    """Check if exception is a rate limit error."""
    return "rate" in exception_str and "limit" in exception_str


def _is_quota_error(exception_str: str) -> bool:
    """Check if exception is a quota/billing error."""
    return "quota" in exception_str or "billing" in exception_str


def _is_llm_provider_error(exception_type: str) -> bool:
    """Check if exception is from LLM provider."""
    providers = ["openai", "anthropic", "google", "langchain"]
    return any(provider in exception_type.lower() for provider in providers)


def _is_extraction_error(exception_type: str) -> bool:
    """Check if exception is an extraction error."""
    keywords = ["extraction", "extract"]
    return any(keyword in exception_type.lower() for keyword in keywords)


def _is_loader_error(exception_type: str) -> bool:
    """Check if exception is a loader error."""
    return any(keyword in exception_type.lower() for keyword in ["loader", "load"])


def _is_formatter_error(exception_type: str) -> bool:
    """Check if exception is a formatter error."""
    return any(keyword in exception_type.lower() for keyword in ["formatter", "format"])


def _is_config_error(exception_type: str, exception_str: str) -> bool:
    """Check if exception is a configuration error."""
    return "config" in exception_type.lower() or "configuration" in exception_str
