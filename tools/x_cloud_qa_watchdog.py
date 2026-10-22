#!/usr/bin/env python3
"""Independent X cloud publisher/controller QA: report and remediate safely.

Run every five minutes from the existing invisible Windows X watchdog.
GitHub / Codeberg cloud state is READ ONLY. Persist incidents before attempts
to notify the QA issue. Missing GH API credentials never cause incident loss.
Only deterministic known recovery is permitted; NEVER retry an uncertain post.
"""
from __future__ import annotations
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

REPO="UniversoAnthares/anthares-kwai-runner"
API="https://api.github.com/repos/"+REPO
CODEBERG="https://codeberg.org/api/v1/repos/"+REPO
NORTHFLANK="https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run"
ROOT=Path(os.environ.get("ANTHARES_X_WATCHDOG_HOME",
    r"D:\AntharsWork\x-watchdog"))
OUTBOX=ROOT/"cloud-qa-outbox"
PRIMARY="x-codeberg-primary.yml"
SECONDARY="x-anthares-browser-cloud-publisher.yml"
QA_ISSUE=380

def http(url):
    response=requests.get(url,timeout=13,headers={"User-Agent":"anthares-x-qa-watchdog"})
    response.raise_for_status()
    return response.json()

def shell(args):
    r=subprocess.run(args,capture_output=True,text=True,encoding="utf-8",
                     errors="replace",timeout=30,
                     creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if r.returncode:
        raise RuntimeError("X_QA_GH_COMMAND_FAILED")
    return r.stdout

def incident_key(provider,code,run=""):
    import hashlib
    raw=(provider+"|"+code+"|"+run).encode()
    return hashlib.sha256(raw).hexdigest()[:20]

def persist(code,provider,run="",recovery="windows-standby"):
    OUTBOX.mkdir(parents=True,exist_ok=True)
    key=incident_key(provider,code,run)
    path=OUTBOX/(key+".json")
    if path.exists():
        return None
    body={"kind":"X_QA_P0","code":code,"provider":provider,"run":str(run),
          "recovery":recovery,"severity":"P0",
          "time_utc":datetime.now(timezone.utc).isoformat(),
          "reconciled":False,
          "note":"Use Windows publisher if cloud fails. Never retry unclear X post."}
    staged=path.with_suffix(".tmp")
    staged.write_text(json.dumps(body,ensure_ascii=True),encoding="utf-8")
    os.replace(staged,path)
    return path

def flush():
    for path in sorted(OUTBOX.glob("*.json"))[:32]:
        try:
            record=json.loads(path.read_text(encoding="utf-8"))
            if record.get("reconciled"):
                continue
            msg=("X_CLOUD_QA_P0 "+json.dumps(record,ensure_ascii=True,
                                                separators=(",",":")))
            shell(["gh","api",f"repos/{REPO}/issues/{QA_ISSUE}/comments",
                   "-X","POST","-f","body="+msg])
            # Only acknowledge after the remote issue confirms creation.
            record["reconciled"]=True
            temp=path.with_suffix(".tmp")
            temp.write_text(json.dumps(record,ensure_ascii=True),encoding="utf-8")
            os.replace(temp,path)
            # Kick the central QA router immediately; if its quota is exceeded,
            # the notification remains in the issue and local failover continues.
            try:
                shell(["gh","workflow","run","cortes-qa-p0-publication-watchdog.yml",
                       "-R",REPO,"-r","main"])
            except Exception:
                pass
        except Exception:
            continue

def check_codeberg():
    try:
        rows=http(CODEBERG+"/actions/runs?limit=40").get("workflow_runs") or []
        match=next((row for row in rows
                if row.get("workflow_id")==PRIMARY),None)
        if not match:
            persist("X_CODEBERG_PUBLISHER_NOT_STARTED","codeberg","no_production_run")
            return
        status=str(match.get("status") or "")
        rid=str(match.get("id") or "unknown")
        if status in ("failure","cancelled","error"):
            persist("X_CODEBERG_PUBLISHER_FAILED","codeberg",rid)
        elif status=="success":
            # A successful smoke-test run never proves X authenticated.
            if str(match.get("event") or "")!="schedule":
                persist("X_CODEBERG_AUTHENTICATED_SCHEDULE_NOT_PROVEN",
                        "codeberg",rid)
        elif status in ("waiting","queued","pending"):
            stamp=match.get("created") or match.get("started")
            if stamp:
                age=(datetime.now(timezone.utc)-
                     datetime.fromisoformat(str(stamp).replace("Z","+00:00"))).total_seconds()
                if age>30*60: persist("X_CODEBERG_RUN_STALE","codeberg",rid)
    except Exception as exc:
        persist("X_CODEBERG_CONTROL_UNREACHABLE","codeberg",type(exc).__name__)

def check_github():
    try:
        body=json.loads(shell(["gh","api",f"repos/{REPO}/actions/workflows/"
                                       f"{SECONDARY}/runs?per_page=8"]))
        runs=body.get("workflow_runs") or []
        latest=next((row for row in runs if row.get("status")=="completed"),None)
        if not latest:
            return
        if latest.get("conclusion") in ("failure","timed_out","cancelled"):
            persist("X_GITHUB_CLOUD_NOT_HEALTHY","github",str(latest.get("id")))
    except Exception as exc:
        persist("X_GITHUB_CLOUD_CONTROL_UNREACHABLE","github",type(exc).__name__)

def check_cloud_service():
    try:
        state=http(NORTHFLANK+"/x/health")
        if state.get("ok") is not True or state.get("durable") is not True:
            persist("X_NORTHFLANK_DURABLE_HEALTH_FAILED","northflank","current")
    except Exception as exc:
        persist("X_NORTHFLANK_SERVICE_UNREACHABLE","northflank",type(exc).__name__)

def run():
    ROOT.mkdir(parents=True,exist_ok=True)
    check_codeberg()
    check_github()
    check_cloud_service()
    flush()
    print("X_CLOUD_QA_AUDIT_DONE outbox_pending="+str(sum(
        1 for p in OUTBOX.glob("*.json")
        if not json.loads(p.read_text(encoding="utf-8")).get("reconciled"))))

if __name__=="__main__":
    try:run()
    except Exception as exc:
        persist("X_QA_WATCHDOG_SELF_FAILURE","windows",type(exc).__name__)
        raise
