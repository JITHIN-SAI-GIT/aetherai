import re
import logging
from dataclasses import dataclass
from typing import Optional
from .secret_filter import SecretFilter

logger = logging.getLogger("security.output_validator")

# Patterns that indicate leaked internals
_STACK_TRACE = re.compile(r"(Traceback \(most recent call last\)|File \".*\", line \d+)", re.I)
_INTERNAL_PATH = re.compile(r"(/home/|/var/|/etc/|C:\\Users\\|C:\\Windows\\|/app/|/backend/)")
_RAW_EXCEPTION = re.compile(r"\b(Exception|Error|Traceback):\s+\S+", re.I)


@dataclass
class OutputValidationResult:
    content: str
    secrets_redacted: int = 0
    issues_found: int = 0
    sanitized: bool = False


class OutputValidator:
    """
    Validates every provider response before it reaches the client.
    Wraps SecretFilter and adds stack trace / internal path detection.
    Applied as the last gate before HTTP serialization.
    """

    def __init__(self):
        self._secret_filter = SecretFilter()

    def validate(self, content: str) -> OutputValidationResult:
        issues = 0
        sanitized = False

        # Step 1: Secret redaction
        content, secrets = self._secret_filter.filter(content)
        if secrets:
            issues += secrets
            sanitized = True

        # Step 2: Stack trace stripping
        if _STACK_TRACE.search(content):
            content = _STACK_TRACE.sub("[stack trace removed]", content)
            issues += 1
            sanitized = True
            logger.warning("Stack trace removed from output")

        # Step 3: Internal path stripping
        if _INTERNAL_PATH.search(content):
            content = _INTERNAL_PATH.sub("[path removed]", content)
            issues += 1
            sanitized = True
            logger.warning("Internal path removed from output")

        # Step 4: Raw exception messages
        if _RAW_EXCEPTION.search(content):
            content = _RAW_EXCEPTION.sub("[error removed]", content)
            issues += 1
            sanitized = True
            logger.warning("Raw exception message removed from output")

        return OutputValidationResult(
            content=content,
            secrets_redacted=secrets,
            issues_found=issues,
            sanitized=sanitized,
        )
