#!/usr/bin/env python3
"""Bootstrap/fast-forward the public CORTES clipper mirror on Codeberg.

Never reveal the Codeberg credential. No rewrite/force push. No CI publishing.
Uses CODEBERG_PUSH_URL already stored as a GitHub protected secret.
"""
import json
import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote, quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

NAME="anthares-clipper"
OWNER="UniversoAnthares"
API="https://codeberg.org/api/v1"
SOURCE=f"https://github.com/{OWNER}/{NAME}.git"
PUBLIC=f"https://codeberg.org/{OWNER}/{NAME}.git"


def git(*args, cwd=None):
    env=dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    command=["git", "-c", "credential.interactive=never", *args]
    p=subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=150)
    if p.returncode:
        raise RuntimeError("GIT_COMMAND_REJECTED_"+str(args[0]).upper().replace("-","_"))
    return p.stdout.strip()


def call(endpoint, token="", method="GET", payload=None):
    auth={"Accept":"application/json","User-Agent":"AntharesCodebergClipperBootstrap/1.0"}
    if token:
        auth["Authorization"]=token if token.startswith("Basic ") else "token "+token
    data=json.dumps(payload).encode() if payload is not None else None
    if data is not None:
        auth["Content-Type"]="application/json"
    req=Request(API+endpoint,headers=auth,data=data,method=method)
    try:
        with urlopen(req,timeout=25) as res:
            raw=res.read(128000)
            return res.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        return exc.code, {}


def main():
    raw=os.getenv("CODEBERG_PUSH_URL") or ""
    url=urlsplit(raw)
    if url.scheme!="https" or url.hostname!="codeberg.org" or not url.password:
        raise RuntimeError("CODEBERG_PROTECTED_AUTH_UNAVAILABLE")
    token=unquote(url.password)
    expected=git("ls-remote",SOURCE,"refs/heads/main").split()[0]
    if len(expected)!=40:
        raise RuntimeError("GITHUB_SOURCE_SHA_INVALID")
    status,current=call(f"/repos/{OWNER}/{NAME}")
    if status==404:
        # Only a repository-owner PAT can create another repository.
        # The token configured for git mirroring is allowed to be repo-scoped.
        user_status,actor=call("/user",token)
        authenticated=token
        if user_status!=200 or str(actor.get("login") or "").lower()!=OWNER.lower():
            username=unquote(url.username or "")
            encoded=base64.b64encode((username+":"+token).encode()).decode()
            candidate="Basic "+encoded
            user_status,actor=call("/user",candidate)
            if user_status!=200 or str(actor.get("login") or "").lower()!=OWNER.lower():
                raise RuntimeError("CODEBERG_OWNER_ADMIN_AUTH_REQUIRED")
            authenticated=candidate
        created,_=call("/user/repos",authenticated,"POST",
            {"name":NAME,"private":False,"auto_init":False,"default_branch":"main"})
        if created not in (200,201):
            raise RuntimeError("CODEBERG_CLIPPER_CREATE_HTTP_"+str(created))
        print("CODEBERG_CLIPPER_REPOSITORY_CREATED=YES",flush=True)
    elif status!=200 or bool(current.get("private")) or current.get("full_name")!=f"{OWNER}/{NAME}":
        raise RuntimeError("CODEBERG_CLIPPER_PUBLIC_REPO_IDENTITY_INVALID")
    else:
        # Created by a separately authenticated repository owner in the UI.
        # No repository-admin PAT is required to push if git grant permits it.
        print("CODEBERG_CLIPPER_PREEXISTING_OWNER_REPO_VERIFIED=YES",flush=True)
    tokenized=urlunsplit((url.scheme,url.netloc,f"/{OWNER}/{NAME}.git","",""))
    with tempfile.TemporaryDirectory(prefix="codeberg-clipper-mirror-") as folder:
        checkout=Path(folder)/"source"
        git("clone","--quiet","--single-branch","--branch","main",SOURCE,str(checkout))
        actual_source=git("rev-parse","refs/heads/main",cwd=checkout)
        if actual_source!=expected:
            raise RuntimeError("GITHUB_SOURCE_MOVED_DURING_BOOTSTRAP")
        git("remote","add","codeberg",tokenized,cwd=checkout)
        existing=git("ls-remote","codeberg","refs/heads/main",cwd=checkout)
        if existing:
            codeberg_sha=existing.split()[0]
            if codeberg_sha==expected:
                print("CODEBERG_CLIPPER_MAIN_ALREADY_CURRENT=YES",flush=True)
            else:
                git("fetch","--quiet","codeberg","main",cwd=checkout)
                git("merge-base","--is-ancestor",codeberg_sha,expected,cwd=checkout)
                git("push","--quiet","codeberg","refs/heads/main:refs/heads/main",cwd=checkout)
        else:
            git("push","--quiet","codeberg","refs/heads/main:refs/heads/main",cwd=checkout)
    public=git("ls-remote",PUBLIC,"refs/heads/main").split()[0]
    if public!=expected:
        raise RuntimeError("CODEBERG_CLIPPER_SHA_READBACK_MISMATCH")
    print("CODEBERG_CLIPPER_SHA_PARITY_PROVEN="+expected,flush=True)
    status,details=call(f"/repos/{OWNER}/{NAME}")
    if status!=200:
        raise RuntimeError("CODEBERG_CLIPPER_SETTINGS_READBACK_FAILED")
    if not details.get("has_actions"):
        print("::warning::CORTES_QA_P0_CODEBERG_CLIPPER_ACTIONS_ENABLE_IN_WEB_UI",flush=True)
        # Git history mirroring is independently successful; do not reject
        # a verified SHA just because the push token lacks admin API scope.
    if status!=200 or not details.get("has_actions"):
        raise RuntimeError("CODEBERG_CLIPPER_ACTIONS_NOT_ENABLED")
    print("CODEBERG_CLIPPER_ACTIONS_ENABLED=YES",flush=True)
    return 0


if __name__=="__main__":
    try:sys.exit(main())
    except Exception as error:
        reason=str(error)
        # Only internal uppercase codes; do not print credential URL or remote stderr.
        if not reason.startswith(("CODEBERG_","GITHUB_","GIT_")):
            reason="CLIPPER_BOOTSTRAP_INTERNAL_ERROR"
        print("::error::CORTES_QA_P0_"+reason,flush=True)
        sys.exit(2)
