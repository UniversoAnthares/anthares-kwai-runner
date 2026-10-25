"""Fail-closed provider eligibility and circuit breaker, QA integration contract.

The caller must independently verify credentials, task support, operator approval,
quota and budget. No network calls, secrets, deployments, payment or publication.
"""
from dataclasses import dataclass
from threading import RLock
import time
from typing import Callable, Iterable


class NoEligibleProvider(RuntimeError):
    pass


class ProvidersTemporarilyUnavailable(RuntimeError):
    pass


class UpstreamOutcomeError(RuntimeError):
    def __init__(self, status: int, message: str = "upstream response",
                 retry_after: int | None = None):
        self.status = int(status)
        self.retry_after = retry_after if isinstance(retry_after, int) and retry_after >= 0 else None
        super().__init__(f"upstream_http_{self.status}")


@dataclass(frozen=True)
class ProviderPolicy:
    name: str
    supports_tasks: frozenset[str]
    operator_authorized: bool
    credential_verified: bool
    remaining_quota_verified: bool
    within_spend_budget: bool
    requires_payment: bool = False
    paid_fallback_explicitly_approved: bool = False

    def can_serve(self, task: str) -> bool:
        return bool(
            task in self.supports_tasks and self.operator_authorized
            and self.credential_verified and self.remaining_quota_verified
            and self.within_spend_budget
            and (not self.requires_payment or self.paid_fallback_explicitly_approved)
        )


class CircuitBreaker:
    def __init__(self, *, clock: Callable[[], float] = time.monotonic,
                 server_fail_threshold: int = 2, server_cooldown: int = 90,
                 quota_cooldown: int = 900, payment_cooldown: int = 3600):
        if min(server_fail_threshold, server_cooldown, quota_cooldown, payment_cooldown) <= 0:
            raise ValueError("positive breaker configuration required")
        self.clock = clock
        self.threshold = server_fail_threshold
        self.cooldowns = {"server": server_cooldown, "quota": quota_cooldown,
                          "payment": payment_cooldown}
        self._state: dict[str, tuple[int, float, str]] = {}
        self._lock = RLock()

    def allowed(self, provider: str) -> bool:
        with self._lock:
            _, blocked_until, _ = self._state.get(provider, (0, 0.0, ""))
            return blocked_until <= self.clock()

    def record_success(self, provider: str) -> None:
        with self._lock:
            self._state.pop(provider, None)

    def record_failure(self, provider: str, *, http_status: int | None = None,
                       timeout: bool = False, retry_after: int | None = None) -> str:
        with self._lock:
            count, _, _ = self._state.get(provider, (0, 0.0, ""))
            if http_status in (401, 403):
                self._state[provider] = (0, float("inf"), "auth_denied")
                return "auth_denied"
            if http_status == 402:
                self._state[provider] = (0, self.clock() + self.cooldowns["payment"], "payment_denied")
                return "payment_denied"
            if http_status == 429:
                base = self.cooldowns["quota"]
                delay = max(base, min(int(retry_after), 86400)) if isinstance(retry_after, int) and retry_after >= 0 else base
                self._state[provider] = (0, self.clock() + delay, "quota_cooldown")
                return "quota_cooldown"
            if timeout or (http_status is not None and http_status >= 500):
                count += 1
                self._state[provider] = (
                    count, self.clock() + self.cooldowns["server"] if count >= self.threshold else 0.0,
                    "server_cooldown" if count >= self.threshold else "transient_failure")
                return self._state[provider][2]
            return "non_retryable"

    def status(self, provider: str) -> dict:
        with self._lock:
            count, until, reason = self._state.get(provider, (0, 0.0, ""))
            return {"provider": provider, "open": until > self.clock(),
                    "consecutive_server_errors": count, "reason": reason}


def dispatch(task: str, policies: Iterable[ProviderPolicy], breaker: CircuitBreaker,
             call: Callable[[str], object]) -> tuple[object, str, list[str]]:
    """Route side-effect-free AI calls; never call for publishing/payments."""
    proposals = list(policies)
    if len({p.name for p in proposals}) != len(proposals):
        raise ValueError("ambiguous duplicate provider")
    allowed = [p for p in proposals if p.can_serve(task)]
    if not allowed:
        raise NoEligibleProvider("no_authorized_verified_provider_for_task")
    attempted: list[str] = []
    for candidate in allowed:
        if not breaker.allowed(candidate.name):
            continue
        attempted.append(candidate.name)
        try:
            result = call(candidate.name)
        except UpstreamOutcomeError as exc:
            reason = breaker.record_failure(candidate.name, http_status=exc.status,
                                            retry_after=exc.retry_after)
            if reason in ("auth_denied", "non_retryable"):
                raise
        except TimeoutError:
            breaker.record_failure(candidate.name, timeout=True)
        else:
            breaker.record_success(candidate.name)
            return result, candidate.name, attempted
    raise ProvidersTemporarilyUnavailable("no_authorized_upstream_response")
