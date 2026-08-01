class SecurityViolationError(Exception):
    def __init__(self, reason: str, category: str = "unknown"):
        self.reason = reason
        self.category = category
        super().__init__(f"[{category}] {reason}")


class RateLimitError(SecurityViolationError):
    def __init__(self, limit_type: str, retry_after: float = 60.0):
        self.limit_type = limit_type
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded for {limit_type}", "rate_limit")


class AuthenticationError(SecurityViolationError):
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, "authentication")


class InjectionDetectedError(SecurityViolationError):
    def __init__(self, pattern: str):
        self.pattern = pattern
        super().__init__(f"Prompt injection detected: {pattern!r}", "injection")


class JailbreakDetectedError(SecurityViolationError):
    def __init__(self, pattern: str):
        self.pattern = pattern
        super().__init__(f"Jailbreak attempt detected: {pattern!r}", "jailbreak")


class ContentPolicyError(SecurityViolationError):
    def __init__(self, category: str):
        self.content_category = category
        super().__init__(f"Content policy violation: {category}", "content")


class InputValidationError(SecurityViolationError):
    def __init__(self, field: str, reason: str):
        self.field = field
        super().__init__(f"Invalid input [{field}]: {reason}", "validation")


class AbuseDetectedError(SecurityViolationError):
    def __init__(self, ip: str, ban_seconds: float):
        self.ip = ip
        self.ban_seconds = ban_seconds
        super().__init__(f"IP temporarily banned: {ip}", "abuse")
