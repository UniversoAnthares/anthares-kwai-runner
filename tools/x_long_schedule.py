"""Canonical cross-platform fixed long-video publication slots.

YouTube long-form: 06:30, 15:00, 20:00 in America/Sao_Paulo.
For four non-YouTube long masters, CORTES closes its same-day day at
22:00 America/Campo_Grande, which is the fourth additional fixed slot.
"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Campo_Grande")
YOUTUBE_TZ = ZoneInfo("America/Sao_Paulo")
MAX_LONG_MASTERS = 4
YOUTUBE_FIXED = ((6,30), (15,0), (20,0))

def slots(day: date):
    first = [
        datetime.combine(day, time(h,m), YOUTUBE_TZ).astimezone(TZ)
        for h,m in YOUTUBE_FIXED
    ]
    fourth = datetime.combine(day, time(22,0), TZ)
    if any(x >= y for x,y in zip(first,first[1:]+[fourth])):
        raise ValueError("X_LONGFORM_SCHEDULE_NON_MONOTONIC")
    return (*first, fourth)

def planned_for(day: date, ordinal: int) -> datetime:
    if ordinal not in range(MAX_LONG_MASTERS):
        raise ValueError("X_DAILY_LONGFORM_LIMIT_4")
    return slots(day)[ordinal]

def eligible_time(planned_at: str, now: datetime | None = None) -> bool:
    if not planned_at:
        return False
    try:
        due = datetime.fromisoformat(planned_at.replace("Z","+00:00"))
    except (ValueError,TypeError,AttributeError):
        return False
    if due.tzinfo is None:
        return False
    now=(now or datetime.now(TZ)).astimezone(TZ)
    due=due.astimezone(TZ)
    # A carryforward does not waive today's fixed first slot.
    if due.date() < now.date():
        due = planned_for(now.date(),0)
    return due <= now

def x_post_day(url: str):
    import re
    match = re.fullmatch(r"https://x\.com/lucasyahn/status/([0-9]+)",str(url or ""))
    if not match:return None
    try:
        stamp=((int(match.group(1)) >>22)+1288834974657)/1000
        return datetime.fromtimestamp(stamp,timezone.utc).astimezone(TZ).date()
    except (ValueError,OverflowError,OSError):
        return None
