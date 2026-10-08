#!/usr/bin/env python3
"""Neutral GitHub/GitLab provider router.

The router is deliberately provider-neutral:
- GitHub and GitLab are peers.
- No provider is intrinsically authoritative.
- One operation can hold only one execution lease at a time.
- Failover is allowed only when the current provider is unavailable and
  the target provider has the same verified repository content checkpoint.
- Different provider commit IDs are allowed when an explicit content ID
  (for example the Git tree SHA) proves byte-equivalent repository content.
- Durable persistence belongs to anthares-control; this module is the
  deterministic policy/state-machine layer used by adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class ProviderStatus(str, Enum):
    READY = "READY"
    BLOCKED_QUOTA = "BLOCKED_QUOTA"
    DOWN = "DOWN"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    UNKNOWN = "UNKNOWN"
    BUSY = "BUSY"


class RouterError(RuntimeError):
    pass


class ProviderUnavailable(RouterError):
    pass


class LeaseConflict(RouterError):
    pass


class CheckpointDiverged(RouterError):
    pass


class InvalidLease(RouterError):
    pass


@dataclass(frozen=True)
class ProviderSnapshot:
    provider: str
    repository: str
    ref: str
    head: str
    status: ProviderStatus
    content_id: Optional[str] = None


@dataclass(frozen=True)
class Checkpoint:
    repository: str
    ref: str
    commit: str
    content_id: Optional[str] = None


@dataclass
class Lease:
    operation_id: str
    owner: str
    provider: str
    generation: int
    checkpoint: Checkpoint
    expires_at: float


class DualProviderRouter:
    """Deterministic policy engine for peer Git providers.

    The production control plane should persist leases/checkpoints and expose
    this policy through its API. This class intentionally keeps no external
    credentials and performs no writes to GitHub/GitLab itself.
    """

    def __init__(self, providers=("github", "gitlab"), clock=None):
        if len(set(providers)) < 2:
            raise ValueError("at least two providers are required")
        self.providers = tuple(p.lower() for p in providers)
        self.clock = clock or (lambda: datetime.now(timezone.utc).timestamp())
        self._snapshots: Dict[str, ProviderSnapshot] = {}
        self._leases: Dict[str, Lease] = {}
        self._last_selected = -1

    def update(self, snapshot: ProviderSnapshot) -> None:
        if snapshot.provider.lower() not in self.providers:
            raise ValueError("unknown provider")
        self._snapshots[snapshot.provider.lower()] = ProviderSnapshot(
            snapshot.provider.lower(),
            snapshot.repository,
            snapshot.ref,
            snapshot.head,
            ProviderStatus(snapshot.status),
            snapshot.content_id,
        )

    def snapshot(self, provider: str) -> ProviderSnapshot:
        try:
            return self._snapshots[provider.lower()]
        except KeyError as exc:
            raise ProviderUnavailable(f"no health snapshot for {provider}") from exc

    def _ready(self, provider: str, repository: str, ref: str) -> bool:
        s = self._snapshots.get(provider)
        return bool(
            s
            and s.repository == repository
            and s.ref == ref
            and s.status == ProviderStatus.READY
        )

    def _active_lease(self, operation_id: str) -> Optional[Lease]:
        lease = self._leases.get(operation_id)
        if not lease:
            return None
        if lease.expires_at <= self.clock():
            del self._leases[operation_id]
            return None
        return lease

    def _next_ready_provider(self, repository: str, ref: str) -> Optional[str]:
        ready = [p for p in self.providers if self._ready(p, repository, ref)]
        if not ready:
            return None
        start = (self._last_selected + 1) % len(self.providers)
        ordered = self.providers[start:] + self.providers[:start]
        for provider in ordered:
            if provider in ready:
                self._last_selected = self.providers.index(provider)
                return provider
        return None

    @staticmethod
    def _same_checkpoint(target: ProviderSnapshot, checkpoint: Checkpoint) -> bool:
        if target.head == checkpoint.commit:
            return True
        return bool(
            target.content_id
            and checkpoint.content_id
            and target.content_id == checkpoint.content_id
        )

    def acquire(
        self,
        operation_id: str,
        owner: str,
        repository: str,
        ref: str,
        ttl_seconds: int = 900,
    ) -> Lease:
        active = self._active_lease(operation_id)
        if active:
            if active.owner != owner:
                raise LeaseConflict(
                    f"operation {operation_id} is already leased by {active.owner}"
                )
            if not self._ready(active.provider, repository, ref):
                raise ProviderUnavailable(
                    f"current provider {active.provider} is no longer ready; use failover"
                )
            current = self.snapshot(active.provider)
            # A lease is fenced to the exact provider HEAD it acquired. Even a
            # content-equivalent new commit means someone else wrote concurrently.
            if current.head != active.checkpoint.commit:
                raise CheckpointDiverged(
                    f"current provider {active.provider} moved from "
                    f"{active.checkpoint.commit} to {current.head}"
                )
            active.expires_at = self.clock() + ttl_seconds
            return active

        provider = self._next_ready_provider(repository, ref)
        if provider is None:
            raise ProviderUnavailable("no ready provider")

        current = self.snapshot(provider)
        lease = Lease(
            operation_id=operation_id,
            owner=owner,
            provider=provider,
            generation=1,
            checkpoint=Checkpoint(
                repository,
                ref,
                current.head,
                current.content_id,
            ),
            expires_at=self.clock() + ttl_seconds,
        )
        self._leases[operation_id] = lease
        return lease

    def renew(self, operation_id: str, owner: str, ttl_seconds: int = 900) -> Lease:
        lease = self._active_lease(operation_id)
        if not lease or lease.owner != owner:
            raise InvalidLease(operation_id)
        lease.expires_at = self.clock() + ttl_seconds
        return lease

    def failover(
        self,
        operation_id: str,
        owner: str,
        target_provider: Optional[str] = None,
        ttl_seconds: int = 900,
    ) -> Lease:
        lease = self._active_lease(operation_id)
        if not lease or lease.owner != owner:
            raise InvalidLease(operation_id)

        current = self.snapshot(lease.provider)
        if current.status == ProviderStatus.READY:
            raise LeaseConflict(
                f"provider {lease.provider} is still READY; do not fail over"
            )

        candidates = [
            p
            for p in self.providers
            if p != lease.provider
            and self._ready(p, lease.checkpoint.repository, lease.checkpoint.ref)
        ]
        if target_provider:
            target_provider = target_provider.lower()
            candidates = [p for p in candidates if p == target_provider]

        if not candidates:
            raise ProviderUnavailable("no failover provider is ready")

        target = candidates[0]
        target_snapshot = self.snapshot(target)
        if not self._same_checkpoint(target_snapshot, lease.checkpoint):
            raise CheckpointDiverged(
                f"target {target} content does not match checkpoint "
                f"{lease.checkpoint.commit}"
            )

        lease.provider = target
        lease.generation += 1
        lease.expires_at = self.clock() + ttl_seconds
        return lease

    def complete(self, operation_id: str, owner: str) -> Checkpoint:
        lease = self._active_lease(operation_id)
        if not lease or lease.owner != owner:
            raise InvalidLease(operation_id)
        final = self.snapshot(lease.provider)
        if final.status != ProviderStatus.READY:
            raise ProviderUnavailable(
                f"provider {lease.provider} is not READY at completion"
            )
        del self._leases[operation_id]
        return Checkpoint(final.repository, final.ref, final.head, final.content_id)

    def release(self, operation_id: str, owner: str) -> None:
        lease = self._active_lease(operation_id)
        if not lease or lease.owner != owner:
            raise InvalidLease(operation_id)
        del self._leases[operation_id]


def snapshot_from_dict(data: dict) -> ProviderSnapshot:
    return ProviderSnapshot(
        provider=data["provider"],
        repository=data["repository"],
        ref=data["ref"],
        head=data["head"],
        status=ProviderStatus(data["status"]),
        content_id=data.get("content_id"),
    )
