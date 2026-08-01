import pytest
from app.security.rate_limiter import RateLimiter
from app.security.exceptions import RateLimitError


def test_allows_requests_under_limit():
    rl = RateLimiter()
    for _ in range(5):
        result = rl.check_ip("1.2.3.4")
        assert result.allowed is True


def test_blocks_after_limit_exceeded():
    from app.security import policies
    original = policies.POLICIES.rate_limit_ip_per_minute
    # Patch limit to 3 for test
    import app.security.rate_limiter as rl_mod
    rl = RateLimiter()
    from app.security.rate_limiter import _SlidingWindow
    rl._ip_windows["5.5.5.5"] = _SlidingWindow(max_requests=3)
    rl.check_ip("5.5.5.5")
    rl.check_ip("5.5.5.5")
    rl.check_ip("5.5.5.5")
    with pytest.raises(RateLimitError) as exc:
        rl.check_ip("5.5.5.5")
    assert exc.value.limit_type == "ip"


def test_different_ips_have_independent_windows():
    rl = RateLimiter()
    from app.security.rate_limiter import _SlidingWindow
    rl._ip_windows["ip-a"] = _SlidingWindow(max_requests=2)
    rl.check_ip("ip-a")
    rl.check_ip("ip-a")
    # ip-b should still be fine
    result = rl.check_ip("ip-b")
    assert result.allowed is True


def test_user_rate_limit_independent():
    rl = RateLimiter()
    result = rl.check_user("user-1")
    assert result.allowed is True
    assert result.limit_type == "user"
