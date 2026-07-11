import time
import math
import logging
from collections import deque
from fastapi import Request, HTTPException, status
from config import settings

logger = logging.getLogger("volunteer_copilot.rate_limiter")

# In-memory storage for rate limiting
# In production, this would use Redis
ip_history = {}  # ip -> list of timestamps
user_history = {}  # user_id/account -> list of timestamps
# key (ip or account) -> {"count": int, "last_failure": float}
auth_failures = {}
default_history = {}
loose_history = {}
strict_history = {}


def get_ip(request: Request) -> str:
    # Handle proxy headers if behind a load balancer
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


class RateLimiter:
    @staticmethod
    def check_limit(key: str, history_dict: dict, limit: int, window_sec: int = 60) -> bool:
        """
        Standard sliding window rate limiter.
        Returns True if allowed, False if blocked.
        """
        now = time.time()
        timestamps = history_dict.get(key)

        if timestamps is None:
            history_dict[key] = deque([now])
            return True

        cutoff = now - window_sec
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps) >= limit:
            return False

        timestamps.append(now)
        return True

    @staticmethod
    def get_backoff_delay(failures: int) -> float:
        """
        Calculates exponential backoff delay.
        0 failures: 0s
        1 failure: 0s
        2 failures: 2s
        3 failures: 4s
        4 failures: 8s
        5+ failures: 16s (capped at 60s max)
        """
        if failures <= 1:
            return 0.0
        # base * 2^(failures - 2)
        delay = 2.0 * math.pow(2, failures - 2)
        return min(delay, 60.0)

    @classmethod
    def check_auth_limit(cls, ip: str, identifier: str = None) -> float:
        """
        Combines IP & Account checks with exponential backoff on failures.
        Returns 0.0 if allowed, or a float representing retry-after delay if blocked.
        """
        now = time.time()
        max_delay = 0.0

        # 1. Check IP failures
        ip_fail_key = f"fail:ip:{ip}"
        if ip_fail_key in auth_failures:
            fail_data = auth_failures[ip_fail_key]
            # Clean up stale failures after window (10 mins)
            if now - fail_data["last_failure"] > 600:
                auth_failures.pop(ip_fail_key)
            else:
                delay = cls.get_backoff_delay(fail_data["count"])
                elapsed = now - fail_data["last_failure"]
                if elapsed < delay:
                    max_delay = max(max_delay, delay - elapsed)

        # 2. Check Account/Identifier failures
        if identifier:
            acc_fail_key = f"fail:acc:{identifier}"
            if acc_fail_key in auth_failures:
                fail_data = auth_failures[acc_fail_key]
                # Clean up stale failures after window (15 mins)
                if now - fail_data["last_failure"] > 900:
                    auth_failures.pop(acc_fail_key)
                else:
                    delay = cls.get_backoff_delay(fail_data["count"])
                    elapsed = now - fail_data["last_failure"]
                    if elapsed < delay:
                        max_delay = max(max_delay, delay - elapsed)

        return max_delay

    @classmethod
    def record_auth_failure(cls, ip: str, identifier: str = None):
        """
        Increments failure count for both IP and Account, marking time.
        """
        now = time.time()

        # Record IP failure
        ip_key = f"fail:ip:{ip}"
        if ip_key not in auth_failures:
            auth_failures[ip_key] = {"count": 0, "last_failure": now}
        auth_failures[ip_key]["count"] += 1
        auth_failures[ip_key]["last_failure"] = now

        # Record Account failure
        if identifier:
            acc_key = f"fail:acc:{identifier}"
            if acc_key not in auth_failures:
                auth_failures[acc_key] = {"count": 0, "last_failure": now}
            auth_failures[acc_key]["count"] += 1
            auth_failures[acc_key]["last_failure"] = now

        logger.warning(
            "Auth failure recorded for IP %s / Account %s. Counts: IP(%s)",
            ip,
            identifier,
            auth_failures[ip_key]["count"],
        )

    @classmethod
    def record_auth_success(cls, ip: str, identifier: str = None):
        """
        Resets failure count on successful authentication.
        """
        ip_key = f"fail:ip:{ip}"
        auth_failures.pop(ip_key, None)

        if identifier:
            acc_key = f"fail:acc:{identifier}"
            auth_failures.pop(acc_key, None)

        logger.info(f"Auth success. Reset counters for IP {ip} / Account {identifier}")


# FastAPI Dependency Handlers
async def rate_limit_default(request: Request):
    ip = get_ip(request)
    allowed = RateLimiter.check_limit(ip, default_history, settings.rate_limit_default, 60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests on this endpoint. Please wait a minute."
        )


async def rate_limit_loose(request: Request):
    ip = get_ip(request)
    allowed = RateLimiter.check_limit(ip, loose_history, settings.rate_limit_loose, 60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again shortly."
        )


async def rate_limit_strict(request: Request):
    ip = get_ip(request)
    allowed = RateLimiter.check_limit(ip, strict_history, settings.rate_limit_strict, 60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Strict rate limit exceeded. Please wait before retrying."
        )
