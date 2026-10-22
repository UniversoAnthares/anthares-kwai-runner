#!/usr/bin/env python3
"""Safely enable existing Codeberg repository Actions via existing secret.

Does not print credentials, token, redirect, body, usernames or PII.
Uses owner-admin permission check and immutable target repository.
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API="https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner"
PUBLIC="https://codeberg.org/UniversoAnthares/anthares-kwai-runner.git"
GITHUB="https://github.com/UniversoAnthares/anthares-kwai-runner.git"


def public_sha(url):
    p=subprocess.run(["git","ls-remote",url,"refs/heads/main"],
                     capture_output=True,text=True,timeout=30)
    if p.returncode!=0 or not p.stdout.strip():
        raise RuntimeError("PUBLIC_MAIN_NOT_READABLE")
    return p.stdout.split()[0]


def request(method, auth, payload=None):
    data=None if payload is None else json.dumps(payload).encode("utf-8")
    req=urllib.request.Request(API,method=method,data=data,headers={
        "Authorization":auth, "Accept":"application/json",
        "Content-Type":"application/json",
        "User-Agent":"Anthares-Codeberg-repository-admin/1"})
    try:
        with urllib.request.urlopen(req,timeout=25) as resp:
            return resp.status,json.load(resp)
    except urllib.error.HTTPError as exc:
        return exc.code,{}


def main():
    remote=os.environ.get("CODEBERG_PUSH_URL","")
    parsed=urllib.parse.urlsplit(remote)
    if parsed.scheme!="https" or parsed.hostname!="codeberg.org" or not parsed.password:
        print("CODEBERG_ACTIONS_CONFIG=AUTH_REQUIRED_OR_PUSH_URL_UNSUPPORTED")
        return 2
    user=urllib.parse.unquote(parsed.username or "")
    password=urllib.parse.unquote(parsed.password)
    auths=[
        "Basic "+base64.b64encode((user+":"+password).encode()).decode(),
        "token "+password,
    ]
    authenticated=None
    for header in auths:
        code,doc=request("GET",header)
        if code==200 and doc.get("permissions",{}).get("admin") is True:
            authenticated=header
            break
    if authenticated is None:
        print("CODEBERG_ACTIONS_CONFIG=ADMIN_PERMISSION_OR_API_TOKEN_REQUIRED")
        return 3
    gh=public_sha(GITHUB)
    cb=public_sha(PUBLIC)
    # First enable Actions; only change default branch if the source is
    # absolutely equal to the canonical main checkpoint.
    desired={"has_actions": True}
    if gh==cb:
        desired["default_branch"]="main"
    status,changed=request("PATCH",authenticated,desired)
    if status!=200:
        print("CODEBERG_ACTIONS_CONFIG=API_REJECTED_HTTP_"+str(status))
        return 4
    # Independent readback verifies observable success.
    check=urllib.request.Request(API,headers={"Accept":"application/json",
                          "User-Agent":"Anthares-Codeberg-readback/1"})
    with urllib.request.urlopen(check,timeout=25) as res:
        result=json.load(res)
    enabled=result.get("has_actions") is True
    branch_ok=(gh!=cb or result.get("default_branch")=="main")
    print("CODEBERG_ACTIONS_ENABLED="+str(enabled).upper())
    print("CODEBERG_MAIN_SHA_PARITY_AT_START="+str(gh==cb).upper())
    print("CODEBERG_DEFAULT_BRANCH_MAIN="+str(result.get("default_branch")=="main").upper())
    if not enabled or not branch_ok:
        return 5
    print("CODEBERG_ACTIONS_REPOSITORY_CONFIG_PROOF=PASS")
    return 0


if __name__=="__main__":
    try: sys.exit(main())
    except Exception:
        print("CODEBERG_ACTIONS_CONFIG=READBACK_OR_REMOTE_UNAVAILABLE")
        sys.exit(6)
