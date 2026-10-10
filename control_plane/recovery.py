"""Deterministic lease/heartbeat/retry primitives for unattended Anthares workers."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable


def _now(ts: float | None = None) -> float:
    return datetime.now(timezone.utc).timestamp() if ts is None else float(ts)


@dataclass(frozen=True)
class Lease:
    owner: str
    acquired_at: float
    heartbeat_at: float
    ttl_seconds: int
    generation: int = 1

    def expired(self, now: float | None = None) -> bool:
        return _now(now) - self.heartbeat_at >= self.ttl_seconds

    def heartbeat(self, now: float | None = None) -> "Lease":
        if self.expired(now):
            raise RuntimeError("lease_expired")
        t = _now(now)
        return Lease(self.owner, self.acquired_at, t, self.ttl_seconds, self.generation)


def acquire(current: Lease | None, owner: str, *, ttl_seconds: int = 120, now: float | None = None) -> Lease:
    if not owner:
        raise ValueError("owner_required")
    if ttl_seconds < 10:
        raise ValueError("ttl_too_small")
    t = _now(now)
    if current and not current.expired(t) and current.owner != owner:
        raise RuntimeError("lease_held")
    generation = 1 if current is None else current.generation + (1 if current.owner != owner or current.expired(t) else 0)
    acquired_at = t if current is None or current.owner != owner or current.expired(t) else current.acquired_at
    return Lease(owner, acquired_at, t, ttl_seconds, generation)


def retry_delay(attempt: int, *, base_seconds: int = 5, cap_seconds: int = 300) -> int:
    if attempt < 1:
        raise ValueError("attempt_must_start_at_1")
    return min(cap_seconds, base_seconds * (2 ** (attempt - 1)))


def choose_executor(candidates: Iterable[dict]) -> str:
    """Choose highest-priority healthy executor; never guess if none are healthy."""
    healthy = [c for c in candidates if c.get("healthy") and c.get("name")]
    if not healthy:
        raise RuntimeError("no_healthy_executor")
    healthy.sort(key=lambda c: (int(c.get("priority", 1000)), str(c["name"])))
    return str(healthy[0]["name"])


class LeaseStore:
    """Small JSON store using replace-on-write. Contains metadata only, never session secrets."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self) -> Lease | None:
        if not self.path.exists():
            return None
        row = json.loads(self.path.read_text(encoding="utf-8"))
        return Lease(**row)

    def write(self, lease: Lease) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(asdict(lease), sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)
