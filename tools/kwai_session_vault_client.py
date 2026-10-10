#!/usr/bin/env python3
"""Cloudflare KV session vault client; never logs credentials or ciphertext.

Only GitHub Actions OIDC can authorize access. The archive is encrypted by
kwai_session_state.sh before upload and remains encrypted at rest in KV.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request

BASE="https://anthares-control.anthares1.workers.dev"
AUDIENCE=BASE
ACCOUNT="lucasrosalem"
MAX_BYTES=17_900_000
EXPECTED_VERSION="2026-10-05-queue-fencing-v16"

def get_json(url,headers=None,data=None,timeout=20):
    safe_headers={"User-Agent":"curl/8.5.0","Accept":"application/json"}
    safe_headers.update(headers or {})
    req=urllib.request.Request(url,headers=safe_headers,data=data,
                               method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req,timeout=timeout) as response:
        return json.load(response)

def preflight():
    h=get_json(BASE+"/health")
    if (h.get("version")!=EXPECTED_VERSION or h.get("persistent_state") is not True
            or h.get("queue_bound") is not True or h.get("pc_fallback") is not False):
        raise RuntimeError("cloudflare durable control not ready")

def oidc():
    request_url=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    request_token=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not request_url or not request_token:
        raise RuntimeError("github OIDC unavailable")
    sep="&" if "?" in request_url else "?"
    url=request_url+sep+"audience="+urllib.parse.quote(AUDIENCE,safe="")
    result=get_json(url,{"Authorization":"bearer "+request_token})
    token=result.get("value","")
    if not token or len(token)>16000:
        raise RuntimeError("invalid GitHub OIDC response")
    return {"Authorization":"Bearer "+token,"Content-Type":"application/json"}

def endpoint(probe=False):
    return BASE+"/kwai/session-vault"+("?probe=1" if probe else "")

def probe(headers):
    d=get_json(endpoint(True),headers)
    if d.get("ok") is not True or d.get("persistent") is not True:
        raise RuntimeError("private session vault unavailable")
    print("KWAI_PRIVATE_VAULT_READY=1")
    print("KWAI_PRIVATE_VAULT_HAS_SESSION="+str(int(bool(d.get("available")))))

def pull(headers,path):
    try:
        d=get_json(endpoint(),headers)
    except urllib.error.HTTPError as exc:
        if exc.code==404:
            print("KWAI_PRIVATE_VAULT_SESSION_ABSENT=1")
            return 3
        raise
    if d.get("schema")!="anthares.kwai.vault.v1" or d.get("account")!=ACCOUNT:
        raise RuntimeError("unexpected vault schema or account")
    text=d.get("ciphertext","")
    if not isinstance(text,str) or len(text)>24_000_000:
        raise RuntimeError("invalid encrypted session payload")
    if hashlib.sha256(text.encode("ascii")).hexdigest()!=d.get("sha256"):
        raise RuntimeError("session ciphertext digest mismatch")
    raw=base64.b64decode(text,validate=True)
    if not raw.startswith(b"Salted__") or len(raw)<48 or len(raw)>MAX_BYTES:
        raise RuntimeError("invalid OpenSSL encrypted archive")
    destination=Path(path)
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(destination.parent),prefix=".kwai-vault-")
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,"wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,destination)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print("KWAI_PRIVATE_VAULT_RESTORED_ENCRYPTED=1")
    return 0

def push(headers,path):
    raw=Path(path).read_bytes()
    if not raw.startswith(b"Salted__") or len(raw)<48 or len(raw)>MAX_BYTES:
        raise RuntimeError("unencrypted or oversized Kwai session archive")
    text=base64.b64encode(raw).decode("ascii")
    payload=json.dumps({"account":ACCOUNT,"ciphertext":text,
                        "sha256":hashlib.sha256(text.encode("ascii")).hexdigest()}).encode("utf-8")
    d=get_json(endpoint(),headers,data=payload,timeout=30)
    if d.get("ok") is not True or d.get("stored") is not True:
        raise RuntimeError("private session vault upload not acknowledged")
    print("KWAI_PRIVATE_VAULT_PERSISTED_ENCRYPTED=1")
    return 0

def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("probe","pull","push"))
    p.add_argument("--path",default="kwai-session.enc")
    a=p.parse_args()
    try:
        print("KWAI_PRIVATE_VAULT_STAGE=control_health")
        preflight()
        print("KWAI_PRIVATE_VAULT_STAGE=github_oidc")
        headers=oidc()
        print("KWAI_PRIVATE_VAULT_STAGE=vault_request")
        if a.action=="probe":probe(headers);return 0
        if a.action=="pull":return pull(headers,a.path)
        return push(headers,a.path)
    except urllib.error.HTTPError as exc:
        # HTTP status is safe diagnostic metadata; never log token or body.
        print("KWAI_PRIVATE_VAULT_HTTP_STATUS="+str(exc.code))
        return 1
    except (OSError,ValueError,RuntimeError,urllib.error.URLError) as exc:
        # No exception strings: network errors may include sensitive URLs.
        print("KWAI_PRIVATE_VAULT_ERROR="+type(exc).__name__)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
