#!/usr/bin/env python3
"""Use an existing authorized Codeberg credential to reconcile repo settings.
The token stays in process memory. No token, cookies or credentials are logged.
"""
import json
import os
import sys
from urllib.parse import urlsplit, unquote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API="https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner"

def credential():
    dedicated=os.environ.get("CODEBERG_API_TOKEN","").strip()
    if dedicated:
        return dedicated
    raw=os.environ.get("CODEBERG_PUSH_URL","")
    parts=urlsplit(raw)
    if parts.scheme=="https" and parts.hostname=="codeberg.org" and parts.password:
        return unquote(parts.password)
    return ""

def api(method="GET", payload=None, token=""):
    headers={"Accept":"application/json","User-Agent":"AntharesCodebergSettings/1.0"}
    if token:
        headers["Authorization"]="token "+token
    if payload is not None:
        headers["Content-Type"]="application/json"
    req=Request(API,headers=headers,method=method,
                data=json.dumps(payload).encode() if payload is not None else None)
    with urlopen(req,timeout=20) as res:
        return json.load(res)

def main():
    try:
        repo=api()
        expected={"default_branch":"main","has_actions":True}
        if all(repo.get(k)==v for k,v in expected.items()):
            print("CODEBERG_ADMIN_SETTINGS=ALREADY_CORRECT")
            return 0
        token=credential()
        if not token:
            print("CODEBERG_ADMIN_SETTINGS=AUTH_REQUIRED")
            return 4
        try:
            api("PATCH",expected,token)
        except HTTPError as exc:
            print("CODEBERG_ADMIN_SETTINGS=HTTP_"+str(exc.code))
            return 5
        after=api()
        done=all(after.get(k)==v for k,v in expected.items())
        print("CODEBERG_ADMIN_SETTINGS="+("VERIFIED" if done else "STILL_INCORRECT"))
        return 0 if done else 6
    except HTTPError as exc:
        print("CODEBERG_ADMIN_SETTINGS=HTTP_"+str(exc.code))
        return 7
    except Exception as exc:
        print("CODEBERG_ADMIN_SETTINGS=FAILED_"+type(exc).__name__)
        return 8

if __name__=="__main__":
    sys.exit(main())
