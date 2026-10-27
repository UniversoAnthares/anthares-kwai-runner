#!/usr/bin/env python3
"""Cancel only owned AppVeyor/Bitrise CI builds with provider-structured quota proof.

Running as GitHub scheduled OIDC watcher. A claim in the Neon controller precedes
any remote cancellation; neither uncertain states nor failures trigger fallback.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = "UniversoAnthares/anthares-kwai-runner"
CONTROLLER = "https://anthares-ci-quota-controller.vercel.app/api/provider-cancel"
CODES = {"ci_quota_exceeded", "quota_exceeded", "quota_exhausted",
 "insufficient_quota", "resource_exhausted", "billing_hard_limit_reached",
 "credits_exhausted", "usage_limit_reached", "monthly_quota_exceeded",
 "daily_quota_exceeded"}
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$")
SHA = re.compile(r"^[a-f0-9]{40}$")


def call(url, token, provider, method="GET", body=None):
    headers = {"Authorization": ("Bearer " if provider == "appveyor" else "") + token,
               "Accept": "application/json", "User-Agent": "Anthares-Quota-Watcher/1"}
    raw = None if body is None else json.dumps(body).encode("utf-8")
    if raw is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=raw, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.load(resp) if resp.status != 204 else {}


def reason(item):
    entries = [item.get(key) for key in ("failure_reason","failure_code","error_code","code")]
    entries += [x.get("code") for x in item.get("messages", []) if isinstance(x, dict)]
    for entry in entries:
        if isinstance(entry, str) and entry.strip().lower() in CODES:
            return entry.strip().lower()
    return None


def recent(item):
    raw = item.get("created") or item.get("triggered_at") or item.get("created_at")
    try:
        start = dt.datetime.fromisoformat(str(raw).replace("Z","+00:00"))
        age = (dt.datetime.now(dt.timezone.utc)-start).total_seconds()
        return start.tzinfo is not None and 0 <= age <= 5400
    except (ValueError,TypeError):
        return False


def appveyor_events(token):
    account = os.getenv("APPVEYOR_ACCOUNT", "")
    project = os.getenv("APPVEYOR_PROJECT", "")
    if not token or not IDENT.fullmatch(account) or not IDENT.fullmatch(project):
        print("APPVEYOR=NOT_CONFIGURED")
        return []
    root = "https://ci.appveyor.com/api/projects/"
    base = root + urllib.parse.quote(account) + "/" + urllib.parse.quote(project)
    history = call(base+"/history?recordsNumber=12&branch=main", token, "appveyor")
    if history.get("project",{}).get("repositoryName") != REPO:
        print("APPVEYOR=PROJECT_NOT_OWNED")
        return []
    events = []
    for summary in history.get("builds", [])[:12]:
        version = str(summary.get("version",""))
        if summary.get("branch")!="main" or not recent(summary) or not IDENT.fullmatch(version):
            continue
        value=call(base+"/build/"+urllib.parse.quote(version),token,"appveyor")
        build=value.get("build",{})
        if value.get("project",{}).get("repositoryName")!=REPO:
            continue
        sha=str(build.get("commitId",""))
        code=reason(build)
        if build.get("version")==version and SHA.fullmatch(sha) and code:
            events.append({"provider":"appveyor","target":account+"__"+project+"__"+version,
             "code":code,"sha":sha,"lookup":base+"/build/"+urllib.parse.quote(version),
             "cancel":"https://ci.appveyor.com/api/builds/"+urllib.parse.quote(account)+"/"+
                 urllib.parse.quote(project)+"/"+urllib.parse.quote(version),
             "token":token,"status":str(build.get("status","")).lower(),
             "version":version})
    return events


def bitrise_events(token):
    app=os.getenv("BITRISE_APP_SLUG","")
    if not token or not IDENT.fullmatch(app):
        print("BITRISE=NOT_CONFIGURED")
        return []
    base="https://api.bitrise.io/v0.1/apps/"+urllib.parse.quote(app)
    meta=call(base,token,"bitrise").get("data",{})
    remote=str(meta.get("repo_url",""))
    allowed={"https://github.com/"+REPO,"https://github.com/"+REPO+".git",
             "git@github.com:"+REPO+".git"}
    if remote not in allowed:
        print("BITRISE=PROJECT_NOT_OWNED")
        return []
    listing=call(base+"/builds?limit=12&branch=main",token,"bitrise").get("data",[])
    events=[]
    for summary in listing[:12]:
        slug=str(summary.get("slug",""))
        if summary.get("branch")!="main" or not recent(summary) or not IDENT.fullmatch(slug):
            continue
        url=base+"/builds/"+urllib.parse.quote(slug)
        build=call(url,token,"bitrise").get("data",{})
        sha=str(build.get("commit_hash",""))
        code=reason(build)
        if build.get("slug")==slug and build.get("branch")=="main" and SHA.fullmatch(sha) and code:
            events.append({"provider":"bitrise","target":app+"__"+slug,
             "code":code,"sha":sha,"lookup":url,"cancel":url+"/abort",
             "token":token,"status":str(build.get("status","")),"slug":slug})
    return events


def get_oidc():
    addr=os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL","")
    auth=os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not addr or not auth:
        raise ValueError("MISSING_OIDC")
    url=addr+("&" if "?" in addr else "?")+urllib.parse.urlencode(
        {"audience":"anthares-ci-quota-controller"})
    req=urllib.request.Request(url,headers={"Authorization":"Bearer "+auth})
    with urllib.request.urlopen(req,timeout=10) as resp:
        return json.load(resp)["value"]


def ledger(oidc, payload):
    req=urllib.request.Request(CONTROLLER, data=json.dumps(payload).encode(),
      method="POST", headers={"Authorization":"Bearer "+oidc,
      "Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=18) as resp:
        return json.load(resp)


def terminal(event,row):
    if event["provider"]=="appveyor":
        return row.get("build",{}).get("version")==event["version"] and (
          row.get("build",{}).get("commitId")==event["sha"]) and (
          str(row.get("build",{}).get("status","")).lower() in
          ("failed","cancelled","canceled"))
    data=row.get("data",{})
    return data.get("slug")==event["slug"] and data.get("commit_hash")==event["sha"] and (
        str(data.get("status","")) in ("2","3","4"))


def cancel_owned(event,oidc):
    base={key:event[key] for key in ("provider","target","sha","code")}
    try:
        claim=ledger(oidc,{"phase":"claim",**base})
    except urllib.error.HTTPError as e:
        return "ALREADY_OR_INVALID" if e.code in (400,403,409) else "LEDGER_ERROR"
    except (urllib.error.URLError,OSError,ValueError):
        return "LEDGER_ERROR"
    if claim.get("code")!="CLAIMED":
        return "CLAIM_UNCONFIRMED"
    outcome="CANCEL_UNCONFIRMED"
    try:
        before=call(event["lookup"],event["token"],event["provider"])
        if terminal(event,before):
            outcome="CANCELLED_NO_INDEPENDENT_RESERVE"
        else:
            if event["provider"]=="appveyor":
                if str(before.get("build",{}).get("status","")).lower() not in ("queued","running","starting"):
                    raise ValueError("UNSAFE_SOURCE_STATUS")
                call(event["cancel"],event["token"],"appveyor",method="DELETE")
            else:
                if str(before.get("data",{}).get("status",""))!="0":
                    raise ValueError("UNSAFE_SOURCE_STATUS")
                call(event["cancel"],event["token"],"bitrise",method="POST",
                     body={"abort_reason":"Confirmed provider quota exhaustion",
                           "abort_with_success":False})
            for _ in range(3):
                after=call(event["lookup"],event["token"],event["provider"])
                if terminal(event,after):
                    outcome="CANCELLED_NO_INDEPENDENT_RESERVE"
                    break
                time.sleep(2)
    except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError):
        pass
    try:
        ledger(oidc,{"phase":"report",**base,
                     "owner_token":claim["owner_token"],"outcome":outcome})
    except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError,KeyError):
        return "REPORT_UNCERTAIN"
    return outcome


def main():
    if os.getenv("GITHUB_REPOSITORY")!=REPO:
        print("UNAUTHORIZED_REPOSITORY")
        return 2
    all_events=[]
    providers=[("appveyor",appveyor_events),("bitrise",bitrise_events)]
    for provider,scanner in providers:
        try:
            all_events.extend(scanner(os.getenv(provider.upper()+"_API_TOKEN","")))
        except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError,KeyError,TypeError):
            print(provider.upper()+"=SOURCE_UNAVAILABLE")
    if not all_events:
        print("QUOTA_EVENTS=NO_STRUCTURED_EVENTS")
        return 0
    try:oidc=get_oidc()
    except (urllib.error.HTTPError,urllib.error.URLError,OSError,ValueError,KeyError):
        print("OIDC_UNAVAILABLE")
        return 2
    failed=False
    for event in all_events:
        result=cancel_owned(event,oidc)
        print("QUOTA_PROVIDER="+event["provider"]+" RESULT="+result)
        if result not in ("CANCELLED_NO_INDEPENDENT_RESERVE","ALREADY_OR_INVALID"):
            failed=True
    return 2 if failed else 0


if __name__=="__main__":
    sys.exit(main())
