#!/usr/bin/env python3
"""Canonical CORTES per-account proportional publication plan.

Each platform/account/day has its own history and eligible queue. Its first
*verified* destination publication anchors the day; remaining confirmations
are distributed through 23:00 America/Campo_Grande. This module does not
allocate leases, publish, rewrite source timestamps, or advance another day.
Always recompute after a confirmed post or an inventory/quota change.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

LOCAL_ZONE = ZoneInfo("America/Campo_Grande")
DAY_END = time(23, 0)


@dataclass(frozen=True)
class PublicationPace:
    status: str
    due_at: datetime | None
    deadline_at: datetime
    remaining_today: int
    deferred_due_to_limit: int
    interval_seconds: float | None
    first_confirmed_at: datetime | None
    last_confirmed_at: datetime | None

    def is_due(self, now: datetime) -> bool:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("CORTES_PACING_NAIVE_NOW")
        return self.status == "DUE" and self.due_at is not None and now >= self.due_at


def _aware(value: datetime | None, name: str) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("CORTES_PACING_NAIVE_" + name)
    return value


def plan_publications(
    *,
    now: datetime,
    target_key: str,
    queued: int,
    started_today: int,
    daily_limit: int,
    first_confirmed_at: datetime | None = None,
    last_confirmed_at: datetime | None = None,
    provider_remaining: int | None = None,
    provider_min_gap_seconds: float = 0,
) -> PublicationPace:
    """Return earliest next due time, derived only from confirmed history and quantity.

    The first slot is due immediately when there has not yet been a confirmed
    destination post today. From then on each next due time is:
      last_confirmed + (23:00 - last_confirmed) / remaining_publishable.
    The calculation runs again following each confirmation. An overdue due
    time permits immediate catch-up; an arbitrary minimum-delay rule never
    replaces the proportion. Provider-documented limits may only restrict it.
    """
    _aware(now, "NOW")
    _aware(first_confirmed_at, "FIRST_CONFIRMED")
    _aware(last_confirmed_at, "LAST_CONFIRMED")
    if ":" not in target_key or not all(s.strip() for s in target_key.split(":", 1)):
        raise ValueError("CORTES_PACING_ACCOUNT_TARGET_REQUIRED")
    if not all(isinstance(n, int) and not isinstance(n, bool) and n >= 0
               for n in (queued, started_today, daily_limit)):
        raise ValueError("CORTES_PACING_COUNTS_INVALID")
    if provider_remaining is not None and (
        not isinstance(provider_remaining, int) or provider_remaining < 0):
        raise ValueError("CORTES_PACING_PROVIDER_CAP_INVALID")
    if not (0 <= provider_min_gap_seconds <= 86400):
        raise ValueError("CORTES_PACING_PROVIDER_GAP_INVALID")
    local = now.astimezone(LOCAL_ZONE)
    deadline = datetime.combine(local.date(), DAY_END, LOCAL_ZONE)
    first = first_confirmed_at.astimezone(LOCAL_ZONE) if first_confirmed_at else None
    last = last_confirmed_at.astimezone(LOCAL_ZONE) if last_confirmed_at else None
    if first and first.date() != local.date():
        raise ValueError("CORTES_PACING_FIRST_OUTSIDE_LOCAL_DAY")
    if last and last.date() != local.date():
        raise ValueError("CORTES_PACING_LAST_OUTSIDE_LOCAL_DAY")
    if (first is None) != (last is None) or (first and last and last < first):
        raise ValueError("CORTES_PACING_CONFIRMATION_ORDER_INVALID")
    free = max(0, daily_limit - started_today)
    quota = free if provider_remaining is None else min(free, provider_remaining)
    remaining = min(queued, quota)
    excess = max(0, queued - remaining)
    kw = dict(deadline_at=deadline, remaining_today=remaining,
              deferred_due_to_limit=excess, first_confirmed_at=first,
              last_confirmed_at=last)
    if queued == 0:
        return PublicationPace("IDLE", None, interval_seconds=None, **kw)
    if local >= deadline:
        return PublicationPace("BLOCKED_SAME_DAY_CAPACITY", None, interval_seconds=None, **kw)
    if remaining == 0:
        return PublicationPace(
            "BLOCKED_PLATFORM_LIMIT" if provider_remaining == 0 else "BLOCKED_SAME_DAY_CAPACITY",
            None, interval_seconds=None, **kw)
    if not last:
        return PublicationPace("DUE", now, interval_seconds=None, **kw)
    seconds = (deadline - last).total_seconds() / remaining
    if seconds <= 0:
        return PublicationPace("BLOCKED_SAME_DAY_CAPACITY", None, interval_seconds=None, **kw)
    if provider_min_gap_seconds > seconds:
        # Reject an infeasible projected daily schedule explicitly. The caller
        # can then use the provider's real capacity without inventing results.
        return PublicationPace("BLOCKED_PLATFORM_LIMIT", None, interval_seconds=seconds, **kw)
    next_due = last + timedelta(seconds=seconds)
    return PublicationPace(
        "DUE" if local >= next_due else "WAIT",
        next_due, interval_seconds=seconds, **kw)


def assert_due(pace: PublicationPace, now: datetime) -> None:
    """Independent check at the irreversible provider-submission boundary."""
    if pace.status in ("BLOCKED_SAME_DAY_CAPACITY", "BLOCKED_PLATFORM_LIMIT"):
        raise RuntimeError(pace.status)
    if not pace.is_due(now):
        raise RuntimeError("CORTES_PACING_WAIT_UNTIL_DUE")
