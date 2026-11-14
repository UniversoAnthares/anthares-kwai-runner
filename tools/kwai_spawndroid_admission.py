#!/usr/bin/env python3
"""Offline-only SpawnDroid Hobby capacity and pacing admission for Kwai.

This module never authenticates, leases, transfers media, or publishes.
It consumes *verified external evidence* supplied by the caller and always
leaves production selection to the independent reviewed cloud_cutover gate.
A synthetic fixture is never production evidence.
"""
from __future__ import annotations

import calendar
import json
import math
import re
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ACCOUNTS = ("lucasrosalem", "universoanthares")
TIMEZONE = ZoneInfo("America/Campo_Grande")
HOBBY_SAFE_MAX_MINUTES = 200
MAX_SESSION_SECONDS = 15 * 60
MIN_SAMPLES_PER_ACCOUNT = 3
PHASES = ("requested_at", "ready_at", "authenticated_at", "mp4_loaded_at",
          "published_at", "public_verified_at", "closed_at")


class AdmissionError(ValueError):
    pass


def timestamp(raw):
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if value.tzinfo is None:
            raise ValueError("timezone missing")
        return value.astimezone(timezone.utc)
    except (AttributeError, ValueError, TypeError) as exc:
        raise AdmissionError("invalid_timestamp") from exc


def number(value, name, *, minimum=0):
    if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
        raise AdmissionError("invalid_" + name)
    return float(value)


def integer(value, name, *, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise AdmissionError("invalid_" + name)
    return value


def fresh(when, now, *, max_age_seconds=120):
    delta = (now - timestamp(when)).total_seconds()
    if not 0 <= delta <= max_age_seconds:
        raise AdmissionError("stale_or_future_evidence")


def measured_costs(rows, now):
    """Per-session sample: one independently confirmed post, session ended."""
    if not isinstance(rows, list):
        raise AdmissionError("measurements_missing")
    costs = {account: [] for account in ACCOUNTS}
    unique_sessions = set()
    unique_videos = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("account") not in ACCOUNTS:
            raise AdmissionError("invalid_measurement_account")
        account = row["account"]
        session = row.get("session_id")
        video = row.get("remote_url")
        if (not isinstance(session, str) or not session or session in unique_sessions
                or not isinstance(video, str)
                or not re.fullmatch(
                    rf"https://www\.kwai\.com/@{account}/video/[0-9]+", video)
                or video in unique_videos):
            raise AdmissionError("unverifiable_session_or_video_identity")
        unique_sessions.add(session)
        unique_videos.add(video)
        if row.get("proof_kind") != "independent_public_readback_verified":
            raise AdmissionError("independent_public_proof_missing")
        if row.get("provider_terminal") != "closed":
            raise AdmissionError("session_teardown_unverified")
        try:
            times = [timestamp(row[p]) for p in PHASES]
        except KeyError as exc:
            raise AdmissionError("measurement_phase_missing") from exc
        if any(b <= a for a, b in zip(times, times[1:])):
            raise AdmissionError("measurement_phase_order_invalid")
        if times[-1] > now or times[-1] < now - timedelta(days=30):
            raise AdmissionError("measurement_outdated")
        billed = (times[-1] - times[1]).total_seconds()
        if billed > MAX_SESSION_SECONDS:
            raise AdmissionError("session_exceeds_hobby_limit")
        costs[account].append({
            "billed_seconds": billed,
            "provision_seconds": (times[1] - times[0]).total_seconds(),
            "auth_seconds": (times[2] - times[1]).total_seconds(),
            "transfer_seconds": (times[3] - times[2]).total_seconds(),
            "publish_seconds": (times[4] - times[3]).total_seconds(),
            "proof_seconds": (times[5] - times[4]).total_seconds(),
            "teardown_seconds": (times[6] - times[5]).total_seconds(),
        })
    for account in ACCOUNTS:
        if len(costs[account]) < MIN_SAMPLES_PER_ACCOUNT:
            raise AdmissionError("insufficient_real_samples_" + account)
    return costs


def nearest_rank_p95(values):
    seq = sorted(values)
    return seq[math.ceil(len(seq) * .95) - 1]


def quota_snapshot(snapshot, now):
    """The source must be checked against an authenticated provider response."""
    if not isinstance(snapshot, dict):
        raise AdmissionError("authenticated_quota_missing")
    fresh(snapshot.get("observed_at"), now)
    if (snapshot.get("source") != "authenticated_spawndroid_settings"
            or snapshot.get("plan") != "Hobby"
            or snapshot.get("overage_enabled") is not False
            or snapshot.get("parallel_runners") != 1
            or snapshot.get("device_minutes_limit") != 200):
        raise AdmissionError("free_quota_unverified")
    used = number(snapshot.get("device_minutes_used"), "used_minutes")
    reserved = number(snapshot.get("other_sessions_reserved_minutes"),
                      "other_sessions_reserved_minutes")
    if used > HOBBY_SAFE_MAX_MINUTES or used + reserved > HOBBY_SAFE_MAX_MINUTES:
        raise AdmissionError("free_quota_exhausted")
    return HOBBY_SAFE_MAX_MINUTES - used - reserved


def projected_account_schedule(account, row, now, minimum_spacing_seconds):
    """Neon is the schedule authority. This is a conservative local cross-check."""
    if not isinstance(row, dict):
        raise AdmissionError("neon_account_state_missing")
    if row.get("target_key") != "kwai:" + account:
        raise AdmissionError("neon_target_mismatch")
    if row.get("source") != "authenticated_neon_cortesqueue":
        raise AdmissionError("neon_origin_unverified")
    fresh(row.get("observed_at"), now)
    queued = integer(row.get("queued"), "queued")
    started_today = integer(row.get("started_today"), "started_today", maximum=100)
    confirmed_today = integer(row.get("confirmed_today"), "confirmed_today", maximum=100)
    if confirmed_today > started_today:
        raise AdmissionError("inconsistent_daily_counts")
    inflight = integer(row.get("inflight"), "inflight")
    uncertain = integer(row.get("uncertain"), "uncertain")
    limit = integer(row.get("daily_limit"), "daily_limit", minimum=1, maximum=100)
    if inflight or uncertain:
        return {"status": "RECONCILE_REQUIRED", "next_due_at": None, "day_slots": 0}
    remaining = min(queued, max(0, limit - started_today))
    local_now = now.astimezone(TIMEZONE)
    start = local_now.replace(hour=6, minute=0, second=0, microsecond=0)
    end = local_now.replace(hour=23, minute=0, second=0, microsecond=0)
    if local_now >= end or remaining == 0:
        return {"status": "DAY_CLOSED_OR_EMPTY", "next_due_at": None, "day_slots": 0}
    first = max(local_now, start)
    last_raw = row.get("last_public_at")
    if confirmed_today and not last_raw:
        return {"status": "UNVERIFIED_PUBLIC_CLOCK", "next_due_at": None, "day_slots": 0}
    if last_raw:
        last = timestamp(last_raw).astimezone(TIMEZONE)
        if last.date() != local_now.date() or last > local_now:
            return {"status": "UNVERIFIED_PUBLIC_CLOCK", "next_due_at": None, "day_slots": 0}
        proportional = (end - last).total_seconds() / (remaining + 1)
        first = max(first, last + timedelta(seconds=max(
            proportional, minimum_spacing_seconds)))
    if first >= end:
        return {"status": "DAY_CAPACITY_EXHAUSTED", "next_due_at": None, "day_slots": 0}
    # Keep a spare end slot: every start must be strictly before 23:00.
    slots = min(remaining, int(math.ceil(
        (end - first).total_seconds() / minimum_spacing_seconds)))
    return {"status": "ELIGIBLE_FOR_NEON_RECHECK",
            "next_due_at": first.isoformat(), "day_slots": slots}


def evaluate(document, *, now=None):
    """Plan only: never grants production authorization or creates jobs."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise AdmissionError("now_must_be_timezone_aware")
    now = now.astimezone(timezone.utc)
    if not isinstance(document, dict):
        raise AdmissionError("document_invalid")
    remaining_budget = quota_snapshot(document.get("quota"), now)
    rows = measured_costs(document.get("measurements"), now)
    safety_multiplier = number(document.get("failure_reserve_multiplier"),
                               "failure_reserve_multiplier", minimum=1)
    if safety_multiplier < 1.25 or safety_multiplier > 3:
        raise AdmissionError("failure_reserve_multiplier_outside_bounds")
    minimum_spacing = integer(document.get("minimum_spacing_seconds"),
                              "minimum_spacing_seconds", minimum=60)
    account_cost = {}
    for account in ACCOUNTS:
        p95 = nearest_rank_p95([x["billed_seconds"] for x in rows[account]])
        rounded = math.ceil(p95 * safety_multiplier / 60)
        if rounded * 60 > MAX_SESSION_SECONDS:
            raise AdmissionError("p95_with_reserve_exceeds_session_limit_" + account)
        account_cost[account] = {
            "samples": len(rows[account]),
            "p95_billed_seconds": p95,
            "p95_provision_seconds": nearest_rank_p95(
                [x["provision_seconds"] for x in rows[account]]),
            "reserved_device_minutes_per_post": rounded,
            "phase_p95_seconds": {
                field: nearest_rank_p95([x[field] for x in rows[account]])
                for field in ("auth_seconds", "transfer_seconds",
                              "publish_seconds", "proof_seconds", "teardown_seconds")
            }
        }
    worst = max(x["reserved_device_minutes_per_post"]
                for x in account_cost.values())
    total_monthly = math.floor(remaining_budget / worst)
    local = now.astimezone(TIMEZONE)
    remaining_days = calendar.monthrange(local.year, local.month)[1] - local.day + 1
    sustainable_daily = total_monthly // remaining_days
    schedule_input = document.get("neon")
    if not isinstance(schedule_input, dict):
        raise AdmissionError("neon_snapshot_missing")
    plans = {acc: projected_account_schedule(
        acc, schedule_input.get(acc), now, minimum_spacing) for acc in ACCOUNTS}
    active = sum(plan["day_slots"] for plan in plans.values())
    # One shared Hobby device. No simultaneous sessions; production keeps OFF.
    max_day = min(sustainable_daily, active)
    return {
        "status": "OFFLINE_CAPACITY_ONLY",
        "production_eligible": False,
        "cloud_cutover_enabled": False,
        "device_minutes_remaining": remaining_budget,
        "accounts": account_cost,
        "account_day_windows": plans,
        "maximum_monthly_posts_shared": total_monthly,
        "sustainable_daily_posts_shared": sustainable_daily,
        "recommended_daily_posts_shared": max_day,
        "accounts_share_single_runner": True,
        "remaining_days_in_month": remaining_days,
        "independent_android_and_real_posts_proven_by_this_report": False,
    }


def quota_cancel_disposition(*, http_status, session_owned,
                             provider_cancel_terminal, effect_state,
                             independent_reserve_verified=False):
    """Cancellation disposition only; provider-specific cancel call is required."""
    if http_status == 429:
        return "CONCURRENCY_BUSY_NO_PARALLEL_RETRY"
    if http_status != 402:
        return "NOT_QUOTA_ERROR"
    if session_owned and provider_cancel_terminal is not True:
        return "CANCEL_UNCONFIRMED"
    if effect_state != "NOT_APPLIED":
        return "RECONCILE_REQUIRED"
    if independent_reserve_verified:
        return "TERMINAL_NEW_FENCED_ATTEMPT_PERMITTED"
    return "CANCELLED_NO_INDEPENDENT_RESERVE"


def main():
    try:
        raw = json.load(sys.stdin)
        result = evaluate(raw)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (AdmissionError, ValueError) as exc:
        # Only print known validation category; never dump input or secrets.
        print("KWAI_SPAWNDROID_ADMISSION=BLOCKED:" + str(exc), file=sys.stderr)
        return 20


if __name__ == "__main__":
    raise SystemExit(main())
