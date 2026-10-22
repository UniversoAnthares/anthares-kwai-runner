#!/usr/bin/env python3
"""Codeberg-hosted P0 supervisor independent of GitHub Actions runners.

Monitors both TikTok accounts and both Neon/Cloudflare ingress routes.
Opens deduplicated Codeberg issue with preflight evidence; no video upload
and no destructive GitHub cancellations. Requires only Forgejo job token.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
import urllib.error
import urllib.request

REPO="UniversoAnthares/anthares-kwai-runner"
CODEBERG_API="https://codeberg.org/api/v1"
GH_API="https://api.github.com"
NOW=dt.datetime.now(dt.timezone.utc)
WORKFLOWS={
    "universo.anthares":"cortes-tiktok-publisher.yml",
    "lucasrosalem4":"cortes-tiktok-lucasrosalem4-cloud-publisher.yml",
}
INGRESS={
    "universo.anthares":(
      "https://br-crimson-unit-b89nau08-cortestiktok.compute.c-14.us-east-1.aws.neon.tech/",
      "https://anthares-cortes-tiktok-ha.anthares1.workers.dev/"),
    "lucasrosalem4":(
      "https://br-crimson-unit-b89nau08-cortestiktok4.compute.c-14.us-east-1.aws.neon.tech/",
      "https://anthares-cortes-tiktok-lucas4-ha.anthares1.workers.dev/"),
}

def fetch(url, token=None, method="GET", payload=None):
    h={"Accept":"application/json","User-Agent":"Anthares-Codeberg-QA-P0/1"}
    if token:h["Authorization"]="token "+token
    content=json.dumps(payload,ensure_ascii=False).encode("utf-8") if payload is not None else None
    if content:h["Content-Type"]="application/json"
    req=urllib.request.Request(url,headers=h,data=content,method=method)
    with urllib.request.urlopen(req,timeout=14) as rsp:
        if rsp.status==204:return {}
        return json.loads(rsp.read(1_000_000).decode("utf-8"))

def incident(account,stage,evidence):
    fingerprint=hashlib.sha256((account+"|"+stage+"|"+NOW.date().isoformat()).encode()).hexdigest()[:16]
    return {"account":account,"stage":stage,"url":evidence,"fingerprint":fingerprint}

def inspect():
    alerts=[]
    for account,workflow in WORKFLOWS.items():
        url=GH_API+"/repos/"+REPO+"/actions/workflows/"+workflow+"/runs?per_page=12"
        try:
            obj=fetch(url)
            runs=obj.get("workflow_runs") or []
            for run in runs:
                name=str(run.get("status") or "")
                if name not in ("queued","pending","waiting","requested"):
                    continue
                started=dt.datetime.fromisoformat(str(run["created_at"]).replace("Z","+00:00"))
                if started < NOW-dt.timedelta(minutes=20) and started > NOW-dt.timedelta(hours=10):
                    alerts.append(incident(account,"github_hosted_queued_over_20m",
                        "https://github.com/"+REPO+"/actions/runs/"+str(run.get("id"))))
                    break
            for run in runs[:5]:
                if run.get("conclusion") in ("failure","timed_out"):
                    alerts.append(incident(account,"github_publisher_failed",
                        "https://github.com/"+REPO+"/actions/runs/"+str(run.get("id"))))
                    break
        except (ValueError,TypeError,KeyError,OSError,urllib.error.URLError) as exc:
            alerts.append(incident(account,"github_visibility_lost",
                "https://github.com/"+REPO+"/actions"))
            print("CODEBERG_P0_GH_INSPECT_FAILURE="+type(exc).__name__,flush=True)
        reachable=0
        for index,base in enumerate(INGRESS[account]):
            try:
                health=fetch(base+"?action=health")
                expected="cortes-tiktok-lucas4-neon" if account=="lucasrosalem4" else "cortes-tiktok-neon"
                if health.get("ok") is True and health.get("fencing") is True and health.get("service")==expected:
                    reachable+=1
                else:raise ValueError("invalid_health_contract")
            except (ValueError,TypeError,OSError,urllib.error.URLError):
                alerts.append(incident(account,"neon_primary_down" if index==0 else "cloudflare_ha_down",base))
        if reachable==0:
            alerts.append(incident(account,"all_queue_ingress_down",INGRESS[account][0]))
    return {x["fingerprint"]:x for x in alerts}.values()

def inspect_x():
    """Independent Codeberg-side X publisher QA; no GitHub-hosted runner needed."""
    alerts=[]
    codeberg=CODEBERG_API+"/repos/"+REPO+"/actions/runs?limit=40"
    try:
        data=fetch(codeberg)
        runs=[r for r in (data.get("workflow_runs") or [])
              if r.get("workflow_id")=="x-codeberg-primary.yml"]
        if not runs:
            alerts.append(incident("x/lucasyahn","codeberg_cloud_publisher_missing",
                                   "https://codeberg.org/"+REPO+"/actions"))
        for run in runs[:15]:
            status=str(run.get("status") or "")
            run_id=str(run.get("id") or "")
            evidence="https://codeberg.org/"+REPO+"/actions"
            if status in ("failure","error") and run.get("event")!="push":
                alerts.append(incident("x/lucasyahn","codeberg_cloud_publisher_failed",
                                       evidence+" (run "+run_id+")"))
                break
            if status in ("waiting","queued","pending"):
                raw=run.get("created") or run.get("started")
                try:
                    timestamp=dt.datetime.fromisoformat(str(raw).replace("Z","+00:00"))
                    age=NOW-timestamp
                    if timestamp.year>2020 and dt.timedelta(minutes=12)<age<dt.timedelta(days=1):
                        alerts.append(incident("x/lucasyahn","codeberg_cloud_runner_stalled",
                                               evidence+" (run "+run_id+")"))
                        break
                except (ValueError,TypeError,OverflowError):
                    pass
    except (ValueError,TypeError,KeyError,OSError,urllib.error.URLError):
        alerts.append(incident("x/lucasyahn","codeberg_cloud_control_unreachable",
                               "https://codeberg.org/"+REPO+"/actions"))
    try:
        data=fetch(GH_API+"/repos/"+REPO+
                   "/actions/workflows/x-anthares-browser-cloud-publisher.yml/runs?per_page=12")
        gh=[row for row in (data.get("workflow_runs") or [])
            if row.get("conclusion") in ("failure","timed_out")]
        if gh:
            alerts.append(incident("x/lucasyahn","github_cloud_publisher_failed",
                                   "https://github.com/"+REPO+"/actions/runs/"+
                                   str(gh[0].get("id") or "")))
    except (ValueError,TypeError,KeyError,OSError,urllib.error.URLError):
        alerts.append(incident("x/lucasyahn","github_cloud_visibility_lost",
                               "https://github.com/"+REPO+"/actions"))
    try:
        state=fetch("https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x/health")
        if state.get("ok") is not True:
            alerts.append(incident("x/lucasyahn","northflank_x_health_invalid",
                                   "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x/health"))
        if state.get("vault_ready") is False:
            alerts.append(incident("x/lucasyahn","x_encrypted_vault_unavailable",
                                   "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x/health"))
    except (ValueError,TypeError,OSError,urllib.error.URLError):
        alerts.append(incident("x/lucasyahn","northflank_x_health_unreachable",
                               "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x/health"))
    return {x["fingerprint"]:x for x in alerts}.values()


def report(alerts):
    token=os.environ.get("FORGEJO_TOKEN","")
    if not token:raise RuntimeError("FORGEJO_DEFAULT_TOKEN_MISSING")
    if os.environ.get("FORGEJO_REPOSITORY",REPO)!=REPO:
        raise RuntimeError("FORGEJO_REPO_IDENTITY_MISMATCH")
    url=CODEBERG_API+"/repos/"+REPO+"/issues"
    existing=fetch(url+"?state=open&limit=100",token=token)
    titles=[str(row.get("title") or "") for row in existing]
    opened=0
    for alert in alerts:
        if alert["fingerprint"] in " ".join(titles):
            continue
        title="[QA P0]["+alert["account"]+"]["+alert["fingerprint"]+"] "+alert["stage"]
        is_x=alert["account"]=="x/lucasyahn"
        instructions=("Ação P0 X: inspecionar Codeberg, GitHub, vault e ledger global PostgreSQL;"
                      " recuperar caminhos determinísticos e preservar Windows como contingência;"
                      " registrar diagnóstico na Central QA GitHub #380."
                      " Nunca repetir POST X iniciado/incerto sem conciliação do post real."
                      if is_x else
                      "Ação P0 TikTok: verificar Codeberg, Neon e publicador,"
                      " recuperar com fencing/idempotência e escalar à Central QA GitHub #283."
                      " Nunca repostar corte STARTED/UNCERTAIN sem conciliação TikTok Studio.")
        body=("Monitor primário no Codeberg (independente dos runners do GitHub).\n\n"
             "Falha: "+alert["stage"]+"\nConta: "+alert["account"]+
             "\nEvidência: "+alert["url"]+"\n\n"+instructions+
             "\nNão expor segredos de autenticação.")
        created=fetch(url,token=token,method="POST",payload={"title":title,"body":body})
        if not created.get("number"):raise RuntimeError("CODEBERG_P0_NOT_ACKNOWLEDGED")
        opened+=1
        print("CODEBERG_QA_P0_ISSUE_CREATED account="+alert["account"]+" issue="+str(created["number"]),flush=True)
    return opened

def main():
    alerts=list(inspect())+list(inspect_x())
    opened=report(alerts)
    print("CODEBERG_P0_WATCH_OK alerts="+str(len(alerts))+" new="+str(opened),flush=True)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
