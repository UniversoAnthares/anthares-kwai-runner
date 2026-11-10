"""Fail-closed, read-only Buffer same-day slot gate for Pinterest.

Provider scheduling is authoritative. This gate is evaluated before each
irreversible createPost, never deletes, reschedules, or shares any post.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("America/Campo_Grande")
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _slot(value):
    parts = str(value).split(":")
    if len(parts) != 2:
        raise RuntimeError("PINTEREST_BUFFER_SLOT_INVALID")
    try:
        hh, mm = map(int, parts)
    except (ValueError, TypeError):
        raise RuntimeError("PINTEREST_BUFFER_SLOT_INVALID") from None
    if not 0 <= hh <= 23 or not 0 <= mm <= 59:
        raise RuntimeError("PINTEREST_BUFFER_SLOT_INVALID")
    return f"{hh:02d}:{mm:02d}"


def open_slots_today(api, channel_id: str, now: datetime | None = None) -> list[str]:
    """Return future unbooked local slots; fail closed on incomplete Buffer reads."""
    now = now or datetime.now(ZONE)
    if now.tzinfo is None:
        raise RuntimeError("PINTEREST_BUFFER_TIMEZONE_REQUIRED")
    now = now.astimezone(ZONE)
    channel = (api("query CortesPinterestTodayChannel { channel(input: { id: "
                   + json.dumps(channel_id) +
                   " }) { id timezone isQueuePaused postingSchedule { day paused times } } }")
               .get("channel") or {})
    if (channel.get("id") != channel_id
            or str(channel.get("timezone") or "") != ZONE.key
            or channel.get("isQueuePaused") is not False):
        raise RuntimeError("PINTEREST_BUFFER_CHANNEL_SCHEDULE_UNVERIFIED")
    rows = channel.get("postingSchedule")
    if not isinstance(rows, list):
        raise RuntimeError("PINTEREST_BUFFER_SCHEDULE_MISSING")
    day = DAYS[now.weekday()]
    matches = [r for r in rows if str(r.get("day") or "").lower() == day]
    if len(matches) != 1:
        raise RuntimeError("PINTEREST_BUFFER_WEEKDAY_UNVERIFIED")
    if matches[0].get("paused"):
        return []
    times = matches[0].get("times")
    if not isinstance(times, list):
        raise RuntimeError("PINTEREST_BUFFER_SLOT_LIST_MISSING")
    planned = {_slot(t) for t in times}
    future = {t for t in planned if t > now.strftime("%H:%M")}
    if not future:
        return []

    orgs = ((api("query CortesPinterestTodayOrganizations { account { organizations { id } } }")
            .get("account") or {}).get("organizations") or [])
    if not orgs or len(orgs) > 10:
        raise RuntimeError("PINTEREST_BUFFER_ORGANIZATION_UNVERIFIED")
    booked = set()
    for org in orgs:
        orgid = str(org.get("id") or "")
        if not orgid:
            raise RuntimeError("PINTEREST_BUFFER_ORGANIZATION_UNVERIFIED")
        cursor = None
        for _ in range(5):
            after = ", after: " + json.dumps(cursor) if cursor else ""
            query = (
                "query CortesPinterestTodayBooked { posts(first: 50" + after +
                ", input: { organizationId: " + json.dumps(orgid) +
                ", sort: [{field: dueAt, direction: asc}], "
                "filter: {status: [scheduled], channelIds: [" +
                json.dumps(channel_id) +
                "]} }) { edges { node { id channelId dueAt status } } "
                "pageInfo { hasNextPage endCursor } } }"
            )
            posts = api(query).get("posts")
            if not isinstance(posts, dict) or not isinstance(posts.get("edges"), list):
                raise RuntimeError("PINTEREST_BUFFER_BOOKINGS_UNVERIFIED")
            for edge in posts["edges"]:
                p = (edge or {}).get("node") or {}
                if p.get("channelId") != channel_id or str(p.get("status") or "").lower() != "scheduled":
                    raise RuntimeError("PINTEREST_BUFFER_BOOKING_IDENTITY_MISMATCH")
                due = str(p.get("dueAt") or "")
                try:
                    dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
                except ValueError:
                    raise RuntimeError("PINTEREST_BUFFER_BOOKING_DATE_INVALID") from None
                if dt.tzinfo is None:
                    raise RuntimeError("PINTEREST_BUFFER_BOOKING_TIMEZONE_MISSING")
                dt = dt.astimezone(ZONE)
                if dt.date() == now.date():
                    booked.add(dt.strftime("%H:%M"))
            pageinfo = posts.get("pageInfo") or {}
            if pageinfo.get("hasNextPage") is not True:
                break
            next_cursor = pageinfo.get("endCursor")
            if not next_cursor or next_cursor == cursor:
                raise RuntimeError("PINTEREST_BUFFER_BOOKINGS_PAGINATION_STALLED")
            cursor = next_cursor
        else:
            raise RuntimeError("PINTEREST_BUFFER_BOOKINGS_PAGINATION_EXCEEDED")
    return sorted(future - booked)


def has_open_slot_today(api, channel_id: str, now: datetime | None = None) -> bool:
    return bool(open_slots_today(api, channel_id, now))
