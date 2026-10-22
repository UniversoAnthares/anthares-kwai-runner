#!/usr/bin/env python3
"""QA P0: scan publisher workflows and authenticated WordPress clip failures."""
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

HUB="UniversoAnthares/anthares-kwai-runner"
REPOS=(HUB,"UniversoAnthares/anthares-clipper")
NETWORKS=("pinterest","linkedin","instagram","threads","tiktok","kwai","facebook",
          "youtube","rumble","odysee","bilibili","bluesky","reddit","x")
FAILED={"failed","error","uncertain","publish_uncertain","container_failed","create_uncertain"}
TOKEN=os.environ.get("GITHUB_TOKEN","")
NOW=dt.datetime.now(dt.timezone.utc)

def http(url, method="GET", payload=None, headers=None):
    h={"Accept":"application/vnd.github+json","User-Agent":"CORTES-QA-P0/1"}
    if url.startswith("https://api.github.com/"):
        h["Authorization"]="Bearer "+TOKEN
        h["X-GitHub-Api-Version"]="2022-11-28"
    h.update(headers or {})
    body=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
    if body:h["Content-Type"]="application/json"
    req=urllib.request.Request(url,method=method,headers=h,data=body)
    with urllib.request.urlopen(req,timeout=35) as response:
        return json.load(response)

def marker(*parts):
    return hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:24]

def network_for(value):
    value=str(value or "").lower()
    return next((n for n in NETWORKS if n in value),"cortes-general")

def workflow_incidents():
    output=[]
    unavailable=0
    for repo in REPOS:
        try:
            data=http("https://api.github.com/repos/"+repo+"/actions/runs?per_page=75")
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TypeError) as exc:
            # Repository-scoped GITHUB_TOKEN may read this repo's Actions but
            # lack rights to a second repo. Keep routing local publishers.
            unavailable+=1
            kind="HTTP_"+str(exc.code) if isinstance(exc,urllib.error.HTTPError) else type(exc).__name__
            print("::warning::CORTES_QA_GITHUB_REPO_UNAVAILABLE repo="+repo+" reason="+kind)
            output.append({"id":marker("github-partial-visibility",repo,NOW.date().isoformat()),
                           "network":"cortes-general","stage":"qa_visibility_lost_github_repo",
                           "evidence":"https://github.com/"+repo+"/actions",
                           "description":"Missing Action run visibility for "+repo})
            continue
        for run in data.get("workflow_runs",[]):
            name=str(run.get("name") or "")
            if not re.search(r"cortes|tiktok|kwai|pinterest|threads|instagram|facebook|linkedin|youtube|publish|buffer",name,re.I):
                continue
            if "P0 publication incident" in name:
                continue
            conclusion=run.get("conclusion")
            state=str(run.get("status") or "")
            if conclusion not in ("failure","timed_out") and state not in ("queued","pending","waiting"):
                continue
            try:
                created=dt.datetime.fromisoformat(run["created_at"].replace("Z","+00:00"))
            except (KeyError, ValueError):
                continue
            if created < NOW-dt.timedelta(hours=2):
                continue
            # A runner waiting for more than 12 minutes is an operational
            # outage even without a formal failed job result.
            stalled=state in ("queued","pending","waiting") and (
                NOW-created>dt.timedelta(minutes=12))
            if conclusion not in ("failure","timed_out") and not stalled:
                continue
            rid=str(run.get("id") or "")
            if not rid.isdigit():continue
            # The Pinterest board outage can recur every 15 minutes.
            # One stable P0 fingerprint per workflow/day avoids issue floods
            # while the live run URL remains available in Actions.
            if network_for(name)=="pinterest":
                fingerprint=marker("gha",repo,name,run["conclusion"],created.date().isoformat())
            else:
                fingerprint=marker("gha",repo,rid)
            output.append({"id":fingerprint,"network":network_for(name),
                           "stage":"github_actions_"+(conclusion or "runner_dispatch_stalled"),
                           "evidence":"https://github.com/"+repo+"/actions/runs/"+rid,
                           "description":name[:100]})
    if unavailable==len(REPOS):
        raise RuntimeError("CORTES_QA_GITHUB_ALL_REPOS_INACCESSIBLE")
    return output

def threads_control_incidents():
    """Independent read-only Neon controller probe; no cloud credentials."""
    url=("https://br-crimson-unit-b89nau08-cortesthreadspub.compute."
         "c-14.us-east-1.aws.neon.tech/?action=gate")
    data=http(url)
    if not isinstance(data,dict) or data.get("ok") is not True:
        raise RuntimeError("THREADS_CONTROL_HEALTH_INVALID")
    queued=len(data.get("queued_ids") or [])
    issues=[]
    if queued and data.get("cloud_primary_enabled") is not True:
        issues.append(("cloud_primary_disabled_with_backlog",
                       "Neon queued="+str(queued)+", Windows fallback should remain active"))
    age=NOW-dt.datetime.fromisoformat(str(
        data.get("cloud_heartbeat_at") or "2000-01-01T00:00:00Z").replace("Z","+00:00"))
    if queued and data.get("cloud_primary_enabled") is True and age>dt.timedelta(minutes=16):
        issues.append(("cloud_primary_heartbeat_stale",
                       "Neon heartbeat age="+str(int(age.total_seconds()/60))+" minutes"))
    return [{"id":marker("threads-control",kind,NOW.date().isoformat()),
             "network":"threads","stage":kind,
             "evidence":"https://github.com/"+HUB+"/actions/workflows/cortes-threads-cloud-handoff.yml",
             "description":description} for kind,description in issues]


def wp_incidents():
    site=os.getenv("WP_SITE_URL","").strip().rstrip("/")
    user=os.getenv("WP_USERNAME","").strip()
    password="".join(os.getenv("WP_APP_PASSWORD","").split())
    if not site.startswith("https://") or not user or not password:
        raise RuntimeError("WP_QA_AUTH_UNAVAILABLE")
    b64=base64.b64encode((user+":"+password).encode()).decode()
    data=http(site+"/wp-json/anthares/v1/cortes/state",
              headers={"Authorization":"Basic "+b64})
    failures={}
    for live in [*(data.get("items") or []),data.get("blocker")]:
        if not isinstance(live,dict):continue
        for clip in live.get("clips") or []:
            if not isinstance(clip,dict):continue
            for name,record in (clip.get("networks") or {}).items():
                if not isinstance(record,dict):continue
                status=str(record.get("status") or "").lower()
                if status not in FAILED:continue
                try:
                    when=dt.datetime.fromisoformat(str(record["updated_at"]).replace("Z","+00:00"))
                except (KeyError,ValueError):continue
                if when.tzinfo is None:when=when.replace(tzinfo=dt.timezone.utc)
                if when<NOW-dt.timedelta(hours=24):continue
                # One urgent ticket per platform/failure/day. All failing clips count.
                key=(network_for(name),status,when.date().isoformat())
                failures[key]=failures.get(key,0)+1
    return [{"id":marker("wp",*key),"network":key[0],"stage":key[1],
             "evidence":"https://anthares.us/wp-admin/",
             "description":str(count)+" affected media items on "+key[2]}
            for key,count in sorted(failures.items())]

def known_markers():
    known=set()
    for page in range(1,6):
        issues=http("https://api.github.com/repos/"+HUB+"/issues?state=all&per_page=100&page="+str(page))
        if not issues:break
        for issue in issues:
            hit=re.search(r"QA-P0-FINGERPRINT:([a-f0-9]{24})",str(issue.get("body") or ""))
            if hit:known.add(hit.group(1))
    return known

def labels():
    for label,color in (("QA-P0","B60205"),("publication-failure","D93F0B")):
        try:http("https://api.github.com/repos/"+HUB+"/labels/"+label)
        except urllib.error.HTTPError as exc:
            if exc.code!=404:raise
            http("https://api.github.com/repos/"+HUB+"/labels","POST",
                 {"name":label,"color":color})

def create_issue(item):
    title="[QA P0]["+item["network"]+"] Falha de publicação — CORRIGIR IMEDIATAMENTE"
    body=("QA-P0-FINGERPRINT:"+item["id"]+"\n\n"
          "PRIORIDADE MÁXIMA / CORREÇÃO IMEDIATA.\n\n"
          "Rede: "+item["network"]+"\nEstágio: "+item["stage"]+"\n"
          "Evidência: "+item["evidence"]+"\n"
          "Informação sanitizada: "+item["description"]+"\n\n"
          "AÇÃO EXIGIDA: investigar logs, identificar causa, corrigir o publicador,"
          " testar e confirmar publicação remota. Preservar idempotência, filas e "
          "estado incerto. Se qualquer operação de envio já começou, reconciliar "
          "antes de tentar novamente para evitar duplicatas. "
          "Não registrar tokens nem conteúdo privado. "
          "Esta ocorrência exige atenção imediata, independentemente do QA 12h.")
    return http("https://api.github.com/repos/"+HUB+"/issues","POST",
                {"title":title,"body":body,
                 "labels":["QA-P0","publication-failure"]})

def main():
    if not TOKEN:raise RuntimeError("GITHUB_TOKEN_REQUIRED")
    items=[]
    bad=[]
    for label,fn in (("github",workflow_incidents),("wordpress",wp_incidents),("threads-control",threads_control_incidents)):
        try:
            result=fn()
            items.extend(result)
            print("CORTES_QA_SCAN source="+label+" observations="+str(len(result)))
        except (RuntimeError,urllib.error.URLError,ValueError,TypeError) as exc:
            bad.append(label)
            items.append({"id":marker("source-failure",label,NOW.date().isoformat()),
                          "network":"cortes-general", "stage":"qa_visibility_lost_"+label,
                          "evidence":"https://github.com/"+HUB+"/actions",
                          "description":"P0 audit source inaccessible; investigate credentials or network"})
            print("::error::CORTES_QA_SCAN_FAILED source="+label+" type="+type(exc).__name__)
    labels()
    seen=known_markers()
    posted=0
    for item in items:
        if item["id"] in seen:continue
        if posted>=20:
            print("::warning::CORTES_QA_BACKLOG_REMAINING")
            break
        created=create_issue(item)
        if not created.get("number"):raise RuntimeError("P0_ISSUE_UNCONFIRMED")
        posted+=1
        seen.add(item["id"])
        print("CORTES_QA_P0_CREATED network="+item["network"]+" issue="+str(created["number"]))
    print("CORTES_QA_ROUTER_OK observations="+str(len(items))+" opened="+str(posted)+" sources_failed="+str(len(bad)))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (RuntimeError,urllib.error.URLError,ValueError):
        print("::error::CORTES_QA_ROUTER_FATAL")
        sys.exit(2)
