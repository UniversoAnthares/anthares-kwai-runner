"""CORTES distribution contract: first 20 short masters of each daily source
are reserved independently for Buffer Instagram, Pinterest, and LinkedIn.

Buffer Free may only hold 10 scheduled posts/channel at a time. The 20 are
a rolling reservation (refill after sends), not 20 simultaneous API posts.
Overflow stays eligible for alternate publishers, only after checking
channel-local occupied Buffer slots. Buffer and other paths share the same
(source, segment, destination) identity.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Absolute CORTES business cap PER REAL SOCIAL NETWORK, not per Buffer
# transport, API call or deployment. Atomic enforcement is in Neon migration
# 20261021_cortes_daily_publication_limit_100.sql, on the first started state.
# Other authorized publishing routes share this same database and quota.
CORTES_DAILY_PUBLICATION_LIMIT = 100

BUFFER_LIMIT_PER_SOURCE = 20
CAPACITY_SOFT_LIMIT = 8
COLLISION_PADDING_MINUTES = 15
NETWORKS = ("instagram", "pinterest", "linkedin")
TZ = ZoneInfo("America/Campo_Grande")
TARGETS = {"instagram": "instagram:universoanthares",
           "pinterest": "pinterest:lucasyahn",
           "linkedin": "linkedin:primary"}


def stable_segment(clip: dict) -> tuple:
    segment = str(clip.get("segment_id") or clip.get("clip_id") or "")
    parts = segment.rsplit(":", 2)
    try:
        start = int(parts[-2]) if len(parts) == 3 else int(clip.get("start_seconds"))
        end = int(parts[-1]) if len(parts) == 3 else int(clip.get("end_seconds"))
    except (ValueError, TypeError):
        raise ValueError("CORTES_DISTRIBUTION_MISSING_TIMELINE") from None
    if start < 0 or end <= start:
        raise ValueError("CORTES_DISTRIBUTION_INVALID_TIMELINE")
    return start, end, segment


def partition_source(clips: list[dict], max_buffer: int = BUFFER_LIMIT_PER_SOURCE):
    if max_buffer != BUFFER_LIMIT_PER_SOURCE:
        raise ValueError("CORTES_BUFFER_PRIORITY_LIMIT_FIXED_AT_20")
    ordered = sorted(clips, key=lambda c: stable_segment(c))
    by_segment = {}
    for clip in ordered:
        k = stable_segment(clip)[2]
        if k and k not in by_segment:
            by_segment[k] = clip
    unique = list(by_segment.values())
    return unique[:BUFFER_LIMIT_PER_SOURCE], unique[BUFFER_LIMIT_PER_SOURCE:]


def distribution_per_source(source_id: str, clips: list[dict]):
    preferred, overflow = partition_source(clips)
    return {"source_id": source_id,
            "buffer": {network: [stable_segment(c)[2] for c in preferred]
                       for network in NETWORKS},
            "alternate": {network: [stable_segment(c)[2] for c in overflow]
                          for network in NETWORKS}}


def parse_instant(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("CORTES_BUFFER_CALENDAR_TIMEZONE_REQUIRED")
    return dt.astimezone(TZ)


def reserved_instants(calendar: dict, network: str, start: datetime,
                      end: datetime) -> list[datetime]:
    """Weekly slots are reserved even when no Buffer post is queued yet."""
    if network not in NETWORKS or start.tzinfo is None or end.tzinfo is None:
        raise ValueError("CORTES_BUFFER_CALENDAR_INVALID_SCOPE")
    entry = (calendar.get("channels") or {}).get(network)
    if not isinstance(entry, dict) or entry.get("timezone") != TZ.key:
        raise ValueError("CORTES_BUFFER_CALENDAR_UNVERIFIED")
    if entry.get("queue_paused"):
        raise ValueError("CORTES_BUFFER_CALENDAR_QUEUE_PAUSED")
    names = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
    weekdays = {names.index(str(r["day"]).lower()): r for r in
                entry.get("weekly_schedule", []) if str(r.get("day")).lower() in names}
    a = start.astimezone(TZ)
    b = end.astimezone(TZ)
    if b < a:
        raise ValueError("CORTES_BUFFER_TIME_RANGE_REVERSED")
    points = []
    day = a.date()
    while day <= b.date():
        slot = weekdays.get(day.weekday(), {})
        if not slot.get("paused"):
            for t in slot.get("times", []):
                try:
                    hour, minute = map(int, str(t).split(":")[:2])
                    moment = datetime.combine(day, datetime.min.time(), TZ).replace(
                        hour=hour, minute=minute)
                except (TypeError, ValueError):
                    raise ValueError("CORTES_BUFFER_SLOT_MALFORMED") from None
                if a-timedelta(minutes=COLLISION_PADDING_MINUTES) <= moment <= b+timedelta(minutes=COLLISION_PADDING_MINUTES):
                    points.append(moment)
        day += timedelta(days=1)
    for post in entry.get("queued_posts", []):
        when = parse_instant(post.get("due_at_utc", ""))
        if a-timedelta(minutes=COLLISION_PADDING_MINUTES) <= when <= b+timedelta(minutes=COLLISION_PADDING_MINUTES):
            points.append(when)
    return sorted(set(points))


def alternative_time_allowed(calendar: dict, network: str,
                             desired: datetime, padding_minutes=COLLISION_PADDING_MINUTES) -> bool:
    """Fail closed for missing/stale Buffer observations."""
    if network not in NETWORKS or desired.tzinfo is None:
        raise ValueError("CORTES_ALTERNATE_INVALID_NETWORK_OR_TIME")
    observed = parse_instant(calendar["observed_at_utc"])
    current = datetime.now(TZ)
    if abs((observed-current).total_seconds()) > 30*60:
        raise ValueError("CORTES_BUFFER_CALENDAR_STALE")
    if not 0 < padding_minutes <= 120:
        raise ValueError("CORTES_ALTERNATE_INVALID_MARGIN")
    points = reserved_instants(calendar, network,
                               desired-timedelta(minutes=padding_minutes),
                               desired+timedelta(minutes=padding_minutes))
    return all(abs((desired.astimezone(TZ)-slot).total_seconds()) >
               padding_minutes*60 for slot in points)


def next_alternative_time(calendar: dict, network: str, after: datetime,
                          until: datetime, step_minutes=5):
    """Try remaining same-day slots first, preserving all Buffer windows."""
    if after.tzinfo is None or until.tzinfo is None or until < after:
        raise ValueError("CORTES_ALTERNATE_INVALID_RANGE")
    cursor = after.astimezone(TZ)
    deadline = until.astimezone(TZ)
    while cursor <= deadline:
        if alternative_time_allowed(calendar, network, cursor):
            return cursor
        cursor += timedelta(minutes=step_minutes)
    return None
