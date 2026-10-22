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
from zoneinfo import ZoneInfo

HUB="UniversoAnthares/anthares-kwai-runner"
REPOS=(HUB,"UniversoAnthares/anthares-clipper")
NETWORKS=("pinterest","linkedin","instagram","threads","tiktok","kwai","facebook",
          "youtube","rumble","odysee","bilibili","bluesky","reddit","x")
FAILED={"failed","error","uncertain","publish_uncertain","container_failed","create_uncertain"}
TOKEN=os.environ.get("GITHUB_TOKEN","")
NOW=dt.datetime.now(dt.timezone.utc)
CORTES_NEON_HEALTH="https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/?action=round-health"

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
        if response.status==204:
            return {"ok":True}
        return json.load(response)

def marker(*parts):
    return hashlib.sha256("|".join(map(str,parts)).encode()).hexdigest()[:24]

def network_for(value):
    value=str(value or "").lower()
    return next((n for n in NETWORKS if n in value),"cortes-general")

def codeberg_incidents():
    """Bridge priority Forgejo incidents to the operational GitHub QA executor.

    Read public issue metadata only; never import arbitrary body text, code or
    URLs into the executable controller. Stable IDs prevent alert storms.
    """
    endpoint="https://codeberg.org/api/v1/repos/"+HUB+"/issues?state=open&limit=100"
    entries=http(endpoint,headers={"Accept":"application/json"})
    if not isinstance(entries,list):
        raise RuntimeError("CODEBERG_P0_ISSUES_INVALID")
    output=[]
    pattern=re.compile(
        r"^\[QA P0\]\[([a-zA-Z0-9._/-]{1,64})\]\[([a-f0-9]{16})\] ([a-z0-9_]{3,80})$")
    for item in entries[:100]:
        if not isinstance(item,dict) or item.get("state")!="open":
            continue
        match=pattern.fullmatch(str(item.get("title") or ""))
        if not match:
            continue
        issue_number=item.get("number")
        if not isinstance(issue_number,int) or not 1<=issue_number<=100000000:
            continue
        account,fingerprint,stage=match.groups()
        account=account.lower()
        network=("tiktok" if account in ("lucasrosalem4","universo.anthares")
                 else network_for(account))
        output.append({
            "id":marker("codeberg-qa-p0",issue_number,fingerprint),
            "network":network,
            "stage":"codeberg_"+stage,
            "evidence":"https://codeberg.org/"+HUB+"/issues/"+str(issue_number),
            "description":"Independent Codeberg QA report #"+str(issue_number)+
                          " account="+account+" status="+stage
        })
    return output


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
            # The QA dispatcher and superseded mirror runs are internal
            # orchestration, not social-publication failures. Do not create an
            # incident from ordinary concurrency cancellation: it could
            # recursively saturate the QA controller every five minutes.
            lower=name.lower()
            if ("p0 publication incident" in lower or
                ("qa" in lower and any(t in lower for t in
                     ("controller","executor","watchdog","immediate","incident"))) or
                ("mirror" in lower and "codeberg" in lower)):
                continue
            status=str(run.get("status") or "")
            conclusion=str(run.get("conclusion") or "")
            is_queued=status in ("queued","pending","waiting","requested")
            if not (is_queued or conclusion in ("failure","timed_out")):
                continue
            try:
                created=dt.datetime.fromisoformat(run["created_at"].replace("Z","+00:00"))
            except (KeyError, ValueError):
                continue
            if is_queued and not (NOW-dt.timedelta(hours=8) <= created < NOW-dt.timedelta(minutes=20)):
                continue
            if not is_queued and created < NOW-dt.timedelta(hours=2):
                continue
            rid=str(run.get("id") or "")
            if not rid.isdigit():continue
            # The Pinterest board outage can recur every 15 minutes.
            # One stable P0 fingerprint per workflow/day avoids issue floods
            # while the live run URL remains available in Actions.
            if is_queued:
                fingerprint=marker("gha-stale",repo,name,created.date().isoformat())
            else:
                # One incident per failing workflow/status/day, not per run:
                # retries must not flood the QA dispatcher or Actions queues.
                fingerprint=marker("gha",repo,name,conclusion,created.date().isoformat())
            output.append({"id":fingerprint,"network":network_for(name),
                           "stage":"github_actions_"+("queued_stale" if is_queued else conclusion),
                           "evidence":"https://github.com/"+repo+"/actions/runs/"+rid,
                           "description":name[:100]})
    # De-duplicate by fingerprint within the same scan, independent of
    # backend pagination or repeated failure observations.
    output=list({item["id"]:item for item in output}.values())
    if unavailable==len(REPOS):
        raise RuntimeError("CORTES_QA_GITHUB_ALL_REPOS_INACCESSIBLE")
    return output

def daily_round_incidents():
    """Independent producer alarm even when AI 502 is checkpointed as success."""
    local=NOW.astimezone(ZoneInfo("America/Campo_Grande"))
    # The canonical six-AM producer gets a full hour before first P0.
    if local.hour<7 or local.hour>=21:
        return []
    data=http(CORTES_NEON_HEALTH,headers={"Accept":"application/json"})
    if (data.get("ok") is not True or
            data.get("round_timezone")!="America/Campo_Grande" or
            not isinstance(data.get("today_master_count"),int)):
        raise RuntimeError("CORTES_DAILY_ROUND_HEALTH_INVALID")
    count=data["today_master_count"]
    if count>0:
        return []
    day=local.date().isoformat()
    # A zero Kwai enqueue is not evidence that no clip was produced in WP.
    # Give downstream-specific recovery precedence when any other target has
    # received today's items; keep old health payloads fail-safe.
    downstream=data.get("today_any_destination_count")
    if downstream is not None and (type(downstream) is not int or downstream<0):
        raise RuntimeError("CORTES_DAILY_ROUND_HEALTH_INVALID")
    distributed=bool(downstream)
    return [{"id":marker("cortes-kwai-distribution-zero" if distributed else
                           "cortes-no-daily-master",day),
             "network":"cortes-general",
             "stage":("P0_DAILY_KWAI_DISTRIBUTION_STALLED" if distributed else
                      "P0_DAILY_PRODUCER_ZERO_MASTERS"),
             "evidence":"https://github.com/UniversoAnthares/anthares-clipper/actions",
             "description":("Kwai enqueue count is ZERO, while other Neon targets have new items; "
                            "investigate WordPress-to-Kwai handoff, schedule and idempotent enqueue. "
                            if distributed else
                            "Kwai enqueue count is ZERO; producer status cannot be inferred from this "
                            "counter. Verify WordPress masters, source lock, AI Hub 502/503/504, "
                            "Unicode title gate, media uploads and Neon handoff. ")+
                            "Dispatch only fenced canonical recovery; never manufacture clips."}]


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

def dispatch_controller(issue_number=None):
    """One batch dispatch for a scan; scheduled polling recovers missed events."""
    inputs={}
    if issue_number is not None:
        number=int(issue_number)
        if number<1:raise RuntimeError("QA_P0_INVALID_ISSUE_NUMBER")
        inputs={"issue_number":str(number)}
    result=http("https://api.github.com/repos/"+HUB+
                "/actions/workflows/cortes-qa-p0-controller.yml/dispatches",
                "POST",{"ref":"main","inputs":inputs})
    if not result.get("ok"):
        raise RuntimeError("QA_P0_CONTROLLER_DISPATCH_NOT_ACKNOWLEDGED")
    print("CORTES_QA_P0_CONTROLLER_BATCH_DISPATCHED")
    return True


def main():
    if not TOKEN:raise RuntimeError("GITHUB_TOKEN_REQUIRED")
    items=[]
    bad=[]
    for label,fn in (("github",workflow_incidents),("codeberg",codeberg_incidents),("daily-round",daily_round_incidents),("wordpress",wp_incidents)):
        try:
            result=fn()
            items.extend(result)
            print("CORTES_QA_SCAN source="+label+" observations="+str(len(result)))
        except (RuntimeError,urllib.error.URLError,ValueError,TypeError) as exc:
            bad.append(label)
            items.append({"id":marker("source-failure",label,NOW.date().isoformat()),
                          "network":"cortes-general", "stage":"qa_visibility_lost_"+label,
                          "evidence":("https://codeberg.org/"+HUB+"/issues" if label=="codeberg" else
                                      "https://github.com/"+HUB+"/actions"),
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
    if posted:
        dispatch_controller()
    print("CORTES_QA_ROUTER_OK observations="+str(len(items))+" opened="+str(posted)+" sources_failed="+str(len(bad)))
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except (RuntimeError,urllib.error.URLError,ValueError):
        print("::error::CORTES_QA_ROUTER_FATAL")
        sys.exit(2)
