import re
import math
import logging
from collections import Counter
from typing import List, Tuple, Optional
from .policies import POLICIES

logger = logging.getLogger("security.secret_filter")


# Regex patterns for known secret formats
_SECRET_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("openai_key",      re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("anthropic_key",   re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}")),
    ("jwt_token",       re.compile(r"eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+")),
    ("bearer_token",    re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]{20,}")),
    ("aws_key",         re.compile(r"AKIA[0-9A-Z]{16}")),
    ("aws_secret",      re.compile(r"(?i)aws[_\-]?(secret|access)[_\-]?key[_\-]?=\s*[A-Za-z0-9/+=]{20,}")),
    ("db_url",          re.compile(r"(postgresql|mysql|mongodb)://[^@\s]+:[^@\s]+@")),
    ("env_var_secret",  re.compile(r"(?i)(api[_\-]?key|secret|password|token)\s*=\s*[A-Za-z0-9\-_\.]{8,}")),
    ("private_key",     re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----")),
    ("github_token",    re.compile(r"gh[pousr]_[A-Za-z0-9]{36}")),
]


def _shannon_entropy(s: str) -> float:
    """Compute Shannon entropy of a string. Higher = more random = more likely a secret."""
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def _redact(text: str, match: re.Match) -> str:
    start, end = match.span()
    return text[:start] + "[REDACTED]" + text[end:]


class SecretFilter:
    """
    Applied to AI OUTPUTS only — never to inputs (inputs use injection/jailbreak detectors).
    Uses regex + Shannon entropy to detect and redact secrets from responses.
    """

    def filter(self, content: str) -> Tuple[str, int]:
        """
        Returns (filtered_content, secrets_found_count).
        Replaces matched secrets with [REDACTED].
        """
        if not content:
            return content, 0

        found = 0

        # Pass 1: Named pattern matching
        for label, pattern in _SECRET_PATTERNS:
            def _replace(m, lbl=label):
                nonlocal found
                found += 1
                logger.warning("Secret detected in output", extra={"type": lbl})
                return "[REDACTED]"
            content = pattern.sub(_replace, content)

        # Pass 2: Entropy-based detection (high-entropy long tokens)
        tokens = re.findall(r"[A-Za-z0-9+/=\-_\.]{%d,}" % POLICIES.min_entropy_string_len, content)
        for token in tokens:
            if _shannon_entropy(token) >= POLICIES.entropy_threshold:
                if token not in content:
                    continue
                content = content.replace(token, "[REDACTED]", 1)
                found += 1
                logger.warning("High-entropy string redacted from output",
                               extra={"length": len(token)})

        return content, found
