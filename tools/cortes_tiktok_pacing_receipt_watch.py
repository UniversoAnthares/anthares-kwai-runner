#!/usr/bin/env python3
"""Independent read-only Neon/Cloudflare TikTok pacing audit; never claims/uploads."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0,str(Path(__file__).resolve().parent))
import cortes_tiktok_queue_consumer as queue

BASES=(
    "https://br-crimson-unit-b89nau08-cortestiktok.compute.c-14.us-east-1.aws.neon.tech/",
    "https://anthares-cortes-tiktok-ha.anthares1.workers.dev/",
)
EXPECTED_GUARDS={
    "cortes_tiktok_daily_start_guard_v1",
    "cortes_tiktok_hard_window_06_23_v1",
    "cortes_tiktok_platform_daily_cap_100",
}
ACTIVATION=datetime(2026,11,12,17,13,tzinfo=timezone.utc)
ZONE=ZoneInfo("America/Campo_Grande")

def check(report):
    assert report.get("account")=="universo.anthares","PACING_OWNER_MISMATCH"
    assert report.get("timezone")=="America/Campo_Grande","PACING_ZONE_MISMATCH"
    assert report.get("guards_active") is True,"PACING_GUARD_INACTIVE"
    assert EXPECTED_GUARDS==set(report.get("guards") or {}),"PACING_GUARD_SET_UNEXPECTED"
    assert all(v=="O" for v in report["guards"].values()),"PACING_GUARD_DISABLED"
    slots=report.get("starts")
    assert isinstance(slots,list) and len(slots)<=100,"PACING_DAILY_LIMIT"
    assert int(report.get("started_today",-1))==len(slots),"PACING_RECEIPT_COUNT_MISMATCH"
    assert int(report.get("capacity_used",-1))==len(slots),"PACING_DAILY_CAPACITY_MISMATCH"
    assert report.get("ok") is True,"PACING_SERVER_AUDIT_FAILED"
    assert int(report.get("window_violation_count",-1))==0,"PACING_SERVER_WINDOW_VIOLATION"
    day=report.get("local_day")
    stamps=[]
    governed=0
    for receipt in slots:
        ts=datetime.fromisoformat(str(receipt.get("utc")).replace("Z","+00:00"))
        assert ts.tzinfo is not None,"PACING_NAIVE_RECEIPT"
        local=ts.astimezone(ZONE)
        assert local.strftime("%Y-%m-%d")==day,"PACING_LOCAL_DAY_MISMATCH"
        assert local.strftime("%H:%M:%S") == str(receipt.get("local_time"))[:8],"PACING_LOCAL_CLOCK_MISMATCH"
        if ts>=ACTIVATION:
            governed+=1
            assert (local.hour>=6 and local.hour<23),"PACING_OUTSIDE_WINDOW"
        stamps.append(ts)
    assert stamps==sorted(stamps),"PACING_NONMONOTONIC_RECEIPTS"
    assert int(report.get("governed_start_count",-1))==governed,"PACING_GOVERNED_COUNT_MISMATCH"
    assert int(report.get("legacy_pre_guard_count",-1))==len(slots)-governed,"PACING_LEGACY_BOUNDARY_ERROR"
    # Independent recalculation of the current next due using the admitted
    # events. Historical queue sizes require contemporaneous telemetry.
    now=datetime.fromisoformat(str(report["server_now"]).replace("Z","+00:00"))
    assert now.tzinfo is not None,"PACING_SERVER_TIME_NAIVE"
    mode=str(report.get("mode") or "")
    if mode in ("publish","paced") and report.get("next_due"):
        due=datetime.fromisoformat(str(report["next_due"]).replace("Z","+00:00"))
        delta=(now-due).total_seconds()
        if mode=="paced":
            assert delta<5,"PACING_BACKEND_DUE_ALREADY_PASSED"
        else:
            assert delta>=-5,"PACING_BACKEND_PUBLISH_BEFORE_DUE"
    return {"day":day,"started":len(slots),"governed":governed,
            "legacy":len(slots)-governed,"mode":mode,
            "observed_gaps_seconds":[int((y-x).total_seconds()) for x,y in zip(stamps,stamps[1:])][-15:]}

def main():
    creds=queue.oidc()
    results={}
    for label,base in zip(("neon","cloudflare"),BASES):
        try:
            result=queue.http(base+"?action=pacing-audit",creds,timeout=25)
        except queue.SafeStop as exc:
            # HTTP 409 indicates a live safety-rule violation, never failover.
            if "HTTP_409_" in str(exc):
                raise RuntimeError("PACING_REMOTE_INVARIANT_VIOLATION_"+label.upper()) from exc
            print("CORTES_TIKTOK_PACING_"+label.upper()+"=UNAVAILABLE "+str(exc)[:90],flush=True)
            continue
        except (OSError,TimeoutError) as exc:
            print("CORTES_TIKTOK_PACING_"+label.upper()+"=UNAVAILABLE "+type(exc).__name__,flush=True)
            continue
        # Every reachable provider must independently validate ALL invariants.
        # A semantic failure is terminal, even if the other ingress is healthy.
        proof=check(result)
        results[label]=(result,proof)
        print("CORTES_TIKTOK_PACING_"+label.upper()+"=PASS "+json.dumps(proof,sort_keys=True),flush=True)
    if len(results)==2:
        one,two=(results["neon"][0],results["cloudflare"][0])
        for key in ("account","local_day","started_today","window_violation_count","guards_active","legacy_pre_guard_count","governed_start_count"):
            assert one.get(key)==two.get(key),"PACING_REDUNDANT_PROVIDERS_DIVERGED_"+key
        assert one["starts"]==two["starts"],"PACING_REDUNDANT_RECEIPTS_DIVERGED"
        print("CORTES_TIKTOK_PACING_INDEPENDENT_DUAL_PROVIDERS=PASS",flush=True)
    elif len(results)==1:
        print("CORTES_TIKTOK_PACING_DEGRADED_ONE_PROVIDER=1",flush=True)
    else:
        raise RuntimeError("PACING_BOTH_PROVIDERS_UNAVAILABLE")
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print("CORTES_TIKTOK_PACING_AUDIT_ERROR="+type(exc).__name__+":"+str(exc)[:110],flush=True)
        raise
