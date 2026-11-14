#!/usr/bin/env python3
"""Fail-closed, credential-free two-account authentication gate for SpawnDroid.

This is the integration boundary between the existing Kwai queue/controller
and a verified Appium session. The caller supplies its existing durable CAS
store and official login/identity adapters; this module NEVER reads Android
private app data or operates credentials. No Android session is created here.

A READY verdict is tied to ONE active WebDriver session, account, package,
and a short evidence TTL. End-of-session requires confirmed provider teardown.
Provider session IDs act as bearer credentials; only their SHA-256 fingerprints
are persisted. Never log the raw IDs, cookies, OTPs, UI XML or token responses.

Live Android login and two-session repetition are NOT proven by offline tests.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from hashlib import sha256
import re
from typing import Callable, Optional, Protocol

ACCOUNT_PACKAGES = {
    "@universoanthares": "com.kwai.video",
    "@lucasrosalem": "kwai.lite.video",
}
_SESSION = re.compile(r"^[A-Za-z0-9_-]{8,130}$")
MAX_OBSERVATION_AGE = timedelta(minutes=2)
MAX_READY_AGE = timedelta(minutes=5)


class Status(str, Enum):
    READY = "READY"
    CLOSED = "CLOSED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    AUTH_DENIED = "AUTH_DENIED"
    AUTH_REVOKED = "AUTH_REVOKED"
    AUTH_EXPIRED = "AUTH_EXPIRED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    UPLOAD_UNAVAILABLE = "UPLOAD_UNAVAILABLE"
    QUOTA_BLOCKED = "QUOTA_BLOCKED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TEARDOWN_UNVERIFIED = "TEARDOWN_UNVERIFIED"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    SESSION_REUSED = "SESSION_REUSED"
    SESSION_UNVERIFIED = "SESSION_UNVERIFIED"
    EVIDENCE_EXPIRED = "EVIDENCE_EXPIRED"
    CAS_CONFLICT = "CAS_CONFLICT"


HARD_BLOCKS = frozenset({
    Status.RECONCILE_REQUIRED,
    Status.NEEDS_HUMAN,
    Status.AUTH_DENIED,
    Status.AUTH_REVOKED,
    Status.AUTH_EXPIRED,
    Status.IDENTITY_MISMATCH,
})


class LoginResult(str, Enum):
    COMPLETED = "COMPLETED"
    HUMAN_CHALLENGE = "HUMAN_CHALLENGE"
    DENIED = "DENIED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class IdentityObservation:
    """Only allowlisted metadata returned by an official UI identity probe."""
    account_handle: Optional[str]
    package: str
    authenticated: bool
    uploader_ready: bool
    observed_at: datetime
    challenge_required: bool = False
    valid_until: Optional[datetime] = None


@dataclass(frozen=True)
class RecoveryRecord:
    account: str
    revision: int
    session_fingerprint: str
    status: Status
    strategy: str
    updated_at: datetime
    expires_at: Optional[datetime] = None
    teardown_verified: bool = False


@dataclass(frozen=True)
class Decision:
    account: str
    status: Status
    strategy: str = "NONE"

    @property
    def can_publish(self) -> bool:
        return self.status is Status.READY


class DurableStore(Protocol):
    """Use the existing canonical controller ledger, with atomic per-key CAS."""
    def read(self, account: str) -> Optional[RecoveryRecord]: ...
    def cas(self, account: str, expected_revision: int, new: RecoveryRecord) -> bool: ...


class CallbackCASStore:
    """Adapter to existing controller read/CAS API; never stores credentials."""
    def __init__(self, read: Callable[[str], Optional[RecoveryRecord]],
                 cas: Callable[[str, int, RecoveryRecord], bool]):
        self._read = read
        self._cas = cas

    def read(self, account: str) -> Optional[RecoveryRecord]:
        return self._read(account)

    def cas(self, account: str, expected_revision: int, new: RecoveryRecord) -> bool:
        return self._cas(account, expected_revision, new)


class InMemoryStore:
    """Offline test fixture only; not persistent and NEVER acceptable in production."""
    def __init__(self):
        self.rows: dict[str, RecoveryRecord] = {}

    def read(self, account: str) -> Optional[RecoveryRecord]:
        return self.rows.get(account)

    def cas(self, account: str, expected_revision: int, new: RecoveryRecord) -> bool:
        prev = self.rows.get(account)
        if (prev.revision if prev else 0) != expected_revision:
            return False
        self.rows[account] = new
        return True


IdentityProbe = Callable[[str, str], IdentityObservation]
OfficialLogin = Callable[[str, str], LoginResult]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("aware_utc_timestamp_required")
    return value.astimezone(timezone.utc)


def _session_hash(session_id: str) -> str:
    if not _SESSION.fullmatch(str(session_id or "")):
        raise ValueError("invalid_session_id")
    return sha256(session_id.encode("utf-8")).hexdigest()


class RecoveryCoordinator:
    def __init__(self, *, store: DurableStore, identity_probe: IdentityProbe,
                 official_login: Optional[OfficialLogin] = None,
                 clock: Callable[[], datetime] = utc_now,
                 production: bool = True):
        if production and isinstance(store, InMemoryStore):
            raise ValueError("durable_store_required")
        self.store = store
        self.identity_probe = identity_probe
        self.official_login = official_login
        self.clock = clock

    def _now(self) -> datetime:
        return _utc(self.clock())

    @staticmethod
    def _package(account: str, package: str) -> None:
        if account not in ACCOUNT_PACKAGES:
            raise ValueError("unsupported_account")
        if package != ACCOUNT_PACKAGES[account]:
            raise ValueError("package_account_mismatch")

    def _commit(self, account: str, previous: Optional[RecoveryRecord],
                fingerprint: str, status: Status, strategy: str,
                expires_at: Optional[datetime] = None,
                teardown_verified: bool = False) -> Decision:
        revision = previous.revision if previous else 0
        row = RecoveryRecord(
            account=account, revision=revision + 1,
            session_fingerprint=fingerprint, status=status, strategy=strategy,
            updated_at=self._now(), expires_at=expires_at,
            teardown_verified=teardown_verified,
        )
        if not self.store.cas(account, revision, row):
            return Decision(account, Status.CAS_CONFLICT)
        return Decision(account, status, strategy)

    def preflight(self, account: str, *, queue_clean: bool,
                  quota_available: bool, provider_ready: bool = True) -> Decision:
        """Call BEFORE allocating minutes or uploading content."""
        if account not in ACCOUNT_PACKAGES:
            raise ValueError("unsupported_account")
        prev = self.store.read(account)
        if prev and prev.status in HARD_BLOCKS:
            return Decision(account, prev.status)
        if prev and not prev.teardown_verified:
            return Decision(account, Status.TEARDOWN_UNVERIFIED)
        if not queue_clean:
            return Decision(account, Status.RECONCILE_REQUIRED)
        if not quota_available:
            return Decision(account, Status.QUOTA_BLOCKED)
        if not provider_ready:
            return Decision(account, Status.PROVIDER_UNAVAILABLE)
        return Decision(account, Status.CLOSED, "SAFE_TO_START")

    def verify_new_session(self, account: str, package: str, session_id: str,
                           *, queue_clean: bool, quota_available: bool,
                           previous_teardown_confirmed: bool = False,
                           official_login_permitted: bool = False) -> Decision:
        """Validate identity on the *new* session. No hidden account switches."""
        self._package(account, package)
        fingerprint = _session_hash(session_id)
        previous = self.store.read(account)
        # Never infer teardown from provider's elapsed time or stale UI state.
        if previous and previous.status in HARD_BLOCKS:
            return Decision(account, previous.status)
        if previous and not previous.teardown_verified:
            return Decision(account, Status.TEARDOWN_UNVERIFIED)
        if previous and previous.session_fingerprint == fingerprint:
            return Decision(account, Status.SESSION_REUSED)
        if previous and not previous_teardown_confirmed:
            return Decision(account, Status.TEARDOWN_UNVERIFIED)
        if not queue_clean:
            return self._commit(account, previous, fingerprint,
                                Status.RECONCILE_REQUIRED, "QUEUE")
        if not quota_available:
            return self._commit(account, previous, fingerprint,
                                Status.QUOTA_BLOCKED, "QUOTA")
        try:
            observation = self.identity_probe(account, session_id)
        except Exception:
            return self._commit(account, previous, fingerprint,
                                Status.PROVIDER_UNAVAILABLE, "PROBE")
        strategy = "EXISTING_OFFICIAL_SESSION"
        if not isinstance(observation, IdentityObservation) or observation.package != package:
            return self._commit(account, previous, fingerprint,
                                Status.IDENTITY_MISMATCH, strategy)
        # Verify package and observation freshness before any official login.
        if (self._now() - _utc(observation.observed_at) < timedelta(0) or
                self._now() - _utc(observation.observed_at) > MAX_OBSERVATION_AGE):
            return self._commit(account, previous, fingerprint,
                                Status.EVIDENCE_EXPIRED, strategy)
        if observation.challenge_required:
            return self._commit(account, previous, fingerprint,
                                Status.NEEDS_HUMAN, "CHALLENGE")
        if not observation.authenticated:
            if not official_login_permitted or self.official_login is None:
                return self._commit(account, previous, fingerprint,
                                    Status.NEEDS_HUMAN, "OFFICIAL_LOGIN_REQUIRED")
            try:
                result = self.official_login(account, session_id)
            except Exception:
                result = LoginResult.UNAVAILABLE
            errors = {
                LoginResult.HUMAN_CHALLENGE: Status.NEEDS_HUMAN,
                LoginResult.DENIED: Status.AUTH_DENIED,
                LoginResult.REVOKED: Status.AUTH_REVOKED,
                LoginResult.EXPIRED: Status.AUTH_EXPIRED,
                LoginResult.UNAVAILABLE: Status.PROVIDER_UNAVAILABLE,
            }
            if result in errors:
                return self._commit(account, previous, fingerprint,
                                    errors[result], "OFFICIAL_LOGIN")
            if result is not LoginResult.COMPLETED:
                return self._commit(account, previous, fingerprint,
                                    Status.AUTH_DENIED, "OFFICIAL_LOGIN")
            strategy = "OFFICIAL_LOGIN"
            try:
                observation = self.identity_probe(account, session_id)
            except Exception:
                return self._commit(account, previous, fingerprint,
                                    Status.PROVIDER_UNAVAILABLE, strategy)
        now = self._now()
        if observation.package != package:
            return self._commit(account, previous, fingerprint,
                                Status.IDENTITY_MISMATCH, strategy)
        observed_at = _utc(observation.observed_at)
        if (now - observed_at < timedelta(0) or
                now - observed_at > MAX_OBSERVATION_AGE or
                (observation.valid_until is not None and
                 _utc(observation.valid_until) <= now)):
            return self._commit(account, previous, fingerprint,
                                Status.EVIDENCE_EXPIRED, strategy)
        if observation.challenge_required:
            return self._commit(account, previous, fingerprint,
                                Status.NEEDS_HUMAN, "CHALLENGE")
        if not observation.authenticated or (
                (observation.account_handle or "").strip().lower() != account):
            return self._commit(account, previous, fingerprint,
                                Status.IDENTITY_MISMATCH, strategy)
        if not observation.uploader_ready:
            return self._commit(account, previous, fingerprint,
                                Status.UPLOAD_UNAVAILABLE, strategy)
        until = min(now + MAX_READY_AGE,
                    _utc(observation.valid_until) if observation.valid_until else
                    now + MAX_READY_AGE)
        return self._commit(account, previous, fingerprint, Status.READY,
                            strategy, expires_at=until)

    def assert_publishable(self, account: str, session_id: str,
                           *, queue_clean: bool) -> Decision:
        """Mandatory check BEFORE the uploader's irreversible action."""
        if account not in ACCOUNT_PACKAGES:
            raise ValueError("unsupported_account")
        fingerprint = _session_hash(session_id)
        row = self.store.read(account)
        if not row or row.session_fingerprint != fingerprint:
            return Decision(account, Status.SESSION_UNVERIFIED)
        if row.status is Status.RECONCILE_REQUIRED or not queue_clean:
            return Decision(account, Status.RECONCILE_REQUIRED)
        if row.status is not Status.READY or row.teardown_verified:
            return Decision(account, Status.SESSION_UNVERIFIED)
        if row.expires_at is None or _utc(row.expires_at) <= self._now():
            return Decision(account, Status.EVIDENCE_EXPIRED)
        return Decision(account, Status.READY, row.strategy)

    def mark_uncertain(self, account: str, session_id: str) -> Decision:
        """An ambiguous upload is fenced until the canonical ledger reconciles."""
        if account not in ACCOUNT_PACKAGES:
            raise ValueError("unsupported_account")
        fingerprint = _session_hash(session_id)
        prev = self.store.read(account)
        if prev is None or prev.session_fingerprint != fingerprint:
            return Decision(account, Status.SESSION_UNVERIFIED)
        return self._commit(account, prev, fingerprint,
                            Status.RECONCILE_REQUIRED, "UNCERTAIN_PUBLICATION")

    def confirm_teardown(self, account: str, session_id: str,
                         *, provider_terminal: bool) -> Decision:
        """Caller must obtain terminal proof from the SpawnDroid provider."""
        if account not in ACCOUNT_PACKAGES:
            raise ValueError("unsupported_account")
        fingerprint = _session_hash(session_id)
        prev = self.store.read(account)
        if prev is None or prev.session_fingerprint != fingerprint:
            return Decision(account, Status.SESSION_UNVERIFIED)
        if not provider_terminal:
            return self._commit(account, prev, fingerprint,
                                Status.TEARDOWN_UNVERIFIED, "TEARDOWN")
        # Preserve challenges, denials, revocations, mismatches and uncertain
        # publications across teardown. The authorized owner must resolve
        # these through the canonical controller before allocating again.
        status = prev.status if prev.status in HARD_BLOCKS else Status.CLOSED
        return self._commit(account, prev, fingerprint, status,
                            "PROVIDER_TERMINAL", teardown_verified=True)
