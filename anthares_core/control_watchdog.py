#!/usr/bin/env python3
"""Self-healing Cloudflare v16 watchdog using only GitHub-hosted actions.

Three independent bounded health attempts precede a redeploy. Recovery is
throttled in durable Git-backed state to avoid a runaway dispatch loop.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

URL="https://anthares-control.anthares1.workers.dev/health"
EXPECTED="2026-10-05-queue-fencing-v16"
REPO="UniversoAnthares/anthares-kwai-runner"
COOLDOWN_SECONDS=7200

def health():
    p=subprocess.run(["curl","-fsS","--connect-timeout","8","--max-time","15",
                      "--header","Accept: application/json",URL],
                     capture_output=True,text=True,timeout=20,check=False)
    if p.returncode!=0:raise RuntimeError("control health transport unavailable")
    d=json.loads(p.stdout)
    return (d.get("version")==EXPECTED and d.get("queue_bound") is True and
            d.get("persistent_state") is True and d.get("pc_fallback") is False)

def dispatch():
    if not os.environ.get("GH_TOKEN"):
        raise RuntimeError("GitHub workflow dispatch token unavailable")
    p=subprocess.run(["gh","workflow","run","cloudflare-central-deploy.yml",
                      "--repo",REPO,"--ref","main"],
                     capture_output=True,text=True,timeout=20,check=False)
    if p.returncode!=0:raise RuntimeError("Cloudflare redeploy dispatch failed")

def supervise(path,check=health,redeploy=dispatch,now=None,delay=lambda n:time.sleep(n)):
    now=int(time.time() if now is None else now)
    state_path=Path(path)
    try:state=json.loads(state_path.read_text())
    except (OSError,ValueError):state={}
    if state.get("schema") not in (None,"anthares.core.control-watchdog.v1"):
        raise ValueError("unexpected watchdog state schema")
    ok=False
    for attempt in range(3):
        try:
            if check():
                ok=True
                break
        except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired):
            pass
        if attempt<2:delay(3)
    state["schema"]="anthares.core.control-watchdog.v1"
    state["checked_at"]=now
    state["healthy"]=ok
    status="HEALTHY"
    if ok:
        state["last_healthy_at"]=now
    else:
        last=int(state.get("last_dispatch_at") or 0)
        if now-last<COOLDOWN_SECONDS:
            status="RECOVERY_THROTTLED"
        else:
            try:
                redeploy()
            except (OSError,RuntimeError,subprocess.TimeoutExpired):
                status="RECOVERY_DISPATCH_FAILED"
            else:
                state["last_dispatch_at"]=now
                status="RECOVERY_DISPATCHED"
    state["status"]=status
    state_path.parent.mkdir(parents=True,exist_ok=True)
    tmp=state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state,sort_keys=True,indent=2)+"\n")
    tmp.replace(state_path)
    return {"healthy":ok,"status":status}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--state",required=True)
    p.add_argument("--github-output")
    args=p.parse_args()
    result=supervise(args.state)
    if args.github_output:
        with open(args.github_output,"a") as f:
            f.write("health_ok="+str(result["healthy"]).lower()+"\n")
    print("ANTHARES_CORE_CONTROL="+result["status"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
