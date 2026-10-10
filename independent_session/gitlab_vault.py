#!/usr/bin/env python3
"""Store/retrieve only encrypted session envelopes in a private GitLab project.
No plaintext Android data is accepted by this adapter.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
from pathlib import Path

DEFAULT_PROJECT="87307279"
DEFAULT_BRANCH="duo-main"
PREFIX="session-vault/objects"


def require_env(name):
    v=os.environ.get(name,"").strip()
    if not v:
        raise SystemExit(f"{name}_MISSING")
    return v


def validate_envelope(raw: bytes):
    try:
        obj=json.loads(raw)
    except Exception as e:
        raise SystemExit("VAULT_ENVELOPE_INVALID_JSON") from e
    required={"schema","identity_hash","salt","nonce","ciphertext"}
    if set(obj) != required or obj.get("schema")!="anthares.session.v1":
        raise SystemExit("VAULT_ENVELOPE_SCHEMA_INVALID")
    for key in ("identity_hash","salt","nonce","ciphertext"):
        if not isinstance(obj[key],str) or not re.fullmatch(r"[0-9a-f]+",obj[key]):
            raise SystemExit("VAULT_ENVELOPE_HEX_INVALID")
    if len(obj["identity_hash"])!=64 or len(obj["salt"])!=32 or len(obj["nonce"])!=24 or len(obj["ciphertext"])<32:
        raise SystemExit("VAULT_ENVELOPE_LENGTH_INVALID")
    return obj


def request(method, project, path, token, payload=None):
    encoded=urllib.parse.quote(path,safe="")
    url=f"https://gitlab.com/api/v4/projects/{urllib.parse.quote(str(project),safe='')}/repository/files/{encoded}"
    if method=="GET":
        url += "?ref="+urllib.parse.quote(DEFAULT_BRANCH,safe="")
        data=None
    else:
        data=json.dumps(payload).encode()
    req=urllib.request.Request(url,data=data,method=method,headers={"PRIVATE-TOKEN":token,"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=("put","get"))
    p.add_argument("name")
    p.add_argument("file")
    args=p.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}",args.name):
        raise SystemExit("VAULT_OBJECT_NAME_INVALID")
    token=require_env("GITLAB_VAULT_TOKEN")
    project=os.environ.get("GITLAB_VAULT_PROJECT",DEFAULT_PROJECT)
    path=f"{PREFIX}/{args.name}.json"
    if args.action=="put":
        raw=Path(args.file).read_bytes(); validate_envelope(raw)
        import base64
        payload={"branch":DEFAULT_BRANCH,"commit_message":f"vault: store {args.name}","content":base64.b64encode(raw).decode(),"encoding":"base64"}
        try:
            request("POST",project,path,token,payload)
        except Exception as e:
            if getattr(e,"code",None)==400:
                raise SystemExit("VAULT_OBJECT_ALREADY_EXISTS")
            raise
        print("PRIVATE_VAULT_OBJECT_STORED")
    else:
        import base64
        obj=request("GET",project,path,token)
        raw=base64.b64decode(obj["content"])
        validate_envelope(raw)
        target=Path(args.file)
        if target.exists(): raise SystemExit("VAULT_REFUSE_OVERWRITE")
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"wb") as out: out.write(raw)
        print("PRIVATE_VAULT_OBJECT_FETCHED")

if __name__=="__main__": main()
