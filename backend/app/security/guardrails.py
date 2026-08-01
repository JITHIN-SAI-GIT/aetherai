import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .input_validator import InputValidator
from .prompt_injection import PromptInjectionDetector
from .jailbreak_detector import JailbreakDetector
from .content_filter import ContentFilter
from .rate_limiter import RateLimiter
from .api_key_auth import APIKeyAuth
from .abuse_detector import AbuseDetector
from .output_validator import OutputValidator
from .audit import AuditLogger, audit_logger
from .metrics import SecurityMetrics, security_metrics
from .exceptions import (
    SecurityViolationError, RateLimitError, AuthenticationError,
    InjectionDetectedError, JailbreakDetectedError, ContentPolicyError,
    InputValidationError, AbuseDetectedError,
)

logger = logging.getLogger("security.guardrails")


@dataclass
class SecurityResult:
    allowed: bool
    reason: Optional[str] = None
    category: Optional[str] = None
    http_status: int = 200


class SecurityManager:
    """
    Single public interface for all security checks.
    MUST be called as the first statement in every API handler.
    No request may reach the pipeline without SecurityResult.allowed = True.
    All blocked requests produce an AuditEvent.
    """

    def __init__(
        self,
        input_validator: InputValidator = None,
        injection_detector: PromptInjectionDetector = None,
        jailbreak_detector: JailbreakDetector = None,
        content_filter: ContentFilter = None,
        rate_limiter: RateLimiter = None,
        auth: APIKeyAuth = None,
        abuse_detector: AbuseDetector = None,
        output_validator: OutputValidator = None,
        audit: AuditLogger = None,
        metrics: SecurityMetrics = None,
    ):
        self._input_val = input_validator or InputValidator()
        self._injection = injection_detector or PromptInjectionDetector()
        self._jailbreak = jailbreak_detector or JailbreakDetector()
        self._content = content_filter or ContentFilter()
        self._rate = rate_limiter or RateLimiter()
        self._auth = auth or APIKeyAuth()
        self._abuse = abuse_detector or AbuseDetector()
        self._output_val = output_validator or OutputValidator()
        self._audit = audit or audit_logger
        self._metrics = metrics or security_metrics

    def check(
        self,
        payload: Dict[str, Any],
        ip: str = "0.0.0.0",
        authorization: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> SecurityResult:
        """
        Run all input security checks in order.
        Returns SecurityResult immediately on first failure — subsequent checks are skipped.
        """
        messages = payload.get("messages", [])

        try:
            # 1. Authentication (placeholder — passthrough by default)
            auth_result = self._auth.authenticate(authorization)
            key_prefix = auth_result.api_key_prefix

            # 2. Abuse check (ban check before rate limit)
            if self._abuse.is_banned(ip):
                self._abuse.record_violation(ip)  # this will raise

            # 3. Rate limiting (IP)
            self._rate.check_ip(ip)

            # 4. Input validation
            self._input_val.validate(payload)

            # 5. Prompt injection
            self._injection.scan(messages)

            # 6. Jailbreak detection
            self._jailbreak.scan(messages)

            # 7. Content filtering
            self._content.scan(messages)

            return SecurityResult(allowed=True)

        except AbuseDetectedError as e:
            self._metrics.record_abuse_ban()
            self._audit.record("abuse", e.reason, ip=ip, user_id=user_id)
            return SecurityResult(allowed=False, reason=e.reason, category="abuse", http_status=403)

        except RateLimitError as e:
            self._metrics.record_rate_limit()
            self._audit.record("rate_limit", e.reason, ip=ip, user_id=user_id)
            return SecurityResult(allowed=False, reason=e.reason, category="rate_limit", http_status=429)

        except AuthenticationError as e:
            self._metrics.record_auth_failure()
            self._audit.record("auth", e.reason, ip=ip)
            return SecurityResult(allowed=False, reason=e.reason, category="auth", http_status=401)

        except InputValidationError as e:
            self._metrics.record_validation_error()
            self._audit.record("validation", e.reason, ip=ip, user_id=user_id)
            return SecurityResult(allowed=False, reason=e.reason, category="validation", http_status=400)

        except InjectionDetectedError as e:
            self._metrics.record_injection()
            self._abuse.record_violation(ip)
            self._audit.record("injection", e.reason, ip=ip, user_id=user_id, pattern=e.pattern)
            return SecurityResult(allowed=False, reason="Request blocked by security policy.", category="injection", http_status=400)

        except JailbreakDetectedError as e:
            self._metrics.record_jailbreak()
            self._abuse.record_violation(ip)
            self._audit.record("jailbreak", e.reason, ip=ip, user_id=user_id, pattern=e.pattern)
            return SecurityResult(allowed=False, reason="Request blocked by security policy.", category="jailbreak", http_status=400)

        except ContentPolicyError as e:
            self._metrics.record_content_hit()
            self._audit.record("content", e.reason, ip=ip, user_id=user_id, category=e.content_category)
            return SecurityResult(allowed=False, reason="Request violates content policy.", category="content", http_status=400)

        except SecurityViolationError as e:
            self._metrics.record_blocked()
            self._audit.record("unknown", e.reason, ip=ip)
            return SecurityResult(allowed=False, reason=e.reason, category=e.category, http_status=400)

    def validate_output(self, content: str) -> str:
        """
        Apply secret filter + output validation to every provider response.
        Returns the sanitized content string.
        """
        result = self._output_val.validate(content)
        if result.secrets_redacted:
            self._metrics.record_secret_prevented()
            self._audit.record("secret_leak", f"{result.secrets_redacted} secret(s) redacted from output")
        return result.content
