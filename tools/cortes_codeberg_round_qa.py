#!/usr/bin/env python3
"""Codeberg hosted CORTES/LinkedIn P0 monitor; independent from GitHub runners."""
from __future__ import annotations
import datetime as dt
from tools.cortes_qa_codeberg_p0_watch import fetch,incident,report,REPO,GH_API

NEON="https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/?action=round-health"
WORKFLOWS={
 "linkedin/personal-primary":"cortes-linkedin-personal-fallback-cloud.yml",
 "linkedin/personal-standby":"cortes-linkedin-personal-cloud.yml",
 "linkedin/corporate-buffer":"cortes-buffer-linkedin-cloud.yml",
}

def scan(now=None,reader=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    reader=reader or fetch
    local=now.astimezone(dt.timezone(dt.timedelta(hours=-4)))
    alerts=[]
    if 7<=local.hour<21:
        try:
            health=reader(NEON)
            count=health.get("today_master_count")
            if health.get("ok") is not True or health.get("round_timezone")!="America/Campo_Grande" or type(count) is not int:
                raise ValueError("daily_health_invalid")
            if count==0:
                alerts.append(incident("cortes/daily","producer_zero_masters_urgent",NEON))
        except (OSError,ValueError,TypeError):
            alerts.append(incident("cortes/daily","producer_neon_health_unavailable",NEON))
    for account,workflow in WORKFLOWS.items():
        if local.hour<6 or local.hour>=21:continue
        url=GH_API+"/repos/"+REPO+"/actions/workflows/"+workflow+"/runs?per_page=12"
        try:
            data=reader(url)
            runs=data.get("workflow_runs")
            if not isinstance(runs,list):raise ValueError("missing_workflow_runs")
            queued=False
            recent_success=False
            for row in runs:
                if not isinstance(row,dict):continue
                try: stamp=dt.datetime.fromisoformat(str(row.get("created_at") or "").replace("Z","+00:00"))
                except ValueError:continue
                if stamp.tzinfo is None:continue
                elapsed=now-stamp
                queued|=(row.get("status") in ("queued","pending","waiting","requested") and dt.timedelta(minutes=23)<elapsed<dt.timedelta(hours=12))
                recent_success|=(row.get("conclusion")=="success" and elapsed<dt.timedelta(minutes=25))
            if queued:alerts.append(incident(account,"hosted_runner_stalled_over_23min",url))
            if account=="linkedin/personal-primary" and not recent_success:
                alerts.append(incident(account,"cloud_primary_heartbeat_lost",url))
        except (OSError,ValueError,TypeError):
            alerts.append(incident(account,"github_workflow_visibility_lost",url))
    return list({x["fingerprint"]:x for x in alerts}.values())

def main():
    events=scan()
    # Forgejo job identity and token are enforced by report() in the same
    # hosting environment that has already passed P0 incident-write tests.
    opened=report(events)
    print("CODEBERG_CORTES_LINKEDIN_QA_P0 alerts="+str(len(events))+" opened="+str(opened),flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
