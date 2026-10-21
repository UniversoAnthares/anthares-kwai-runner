#!/usr/bin/env python3
"""One-shot, secret-safe Pinterest OAuth capability probe in GitHub-hosted Actions.
Reads BWS machine-account inventory from stdin. Never prints secret names,
values or request bodies. No write requests to Pinterest or the CORTES ledger.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

def probe():
    rows=json.load(sys.stdin)
    if not isinstance(rows,list):
        raise RuntimeError("BWS_INVENTORY_INVALID")
    found={}
    for row in rows:
        key=str(row.get("key") or "").strip().upper()
        if key in {"PINTEREST_ACCESS_TOKEN","PINTEREST_OAUTH_ACCESS_TOKEN","PINTEREST_BOARD_ID"}:
            found[key]=str(row.get("value") or "").strip()
    print("PIN_BWS_OAUTH_PRESENT="+str(bool(found.get("PINTEREST_ACCESS_TOKEN") or found.get("PINTEREST_OAUTH_ACCESS_TOKEN"))).lower(),flush=True)
    print("PIN_BWS_BOARD_PRESENT="+str(bool(found.get("PINTEREST_BOARD_ID"))).lower(),flush=True)
    token=found.get("PINTEREST_ACCESS_TOKEN") or found.get("PINTEREST_OAUTH_ACCESS_TOKEN")
    if not token:
        return 0
    h={"Authorization":"Bearer "+token,"Accept":"application/json","User-Agent":"AntharesPinterestOAuthReadOnly/1.0"}
    for name,url in [
        ("IDENTITY","https://api.pinterest.com/v5/user_account"),
        ("BOARDS","https://api.pinterest.com/v5/boards?page_size=100"),
    ]:
        try:
            req=urllib.request.Request(url,headers=h)
            with urllib.request.urlopen(req,timeout=16) as resp:
                payload=json.load(resp)
            if name=="IDENTITY":
                print("PIN_OAUTH_IDENTITY_VALID="+str(str(payload.get("username") or "").lower()=="lucasyahn").lower(),flush=True)
            else:
                items=payload.get("items") or []
                print("PIN_OAUTH_BOARD_MATCH="+str(any(str(b.get("id") or "")=="819514532133906920" for b in items)).lower(),flush=True)
        except urllib.error.HTTPError as exc:
            print("PIN_OAUTH_"+name+"_HTTP="+str(exc.code),flush=True)
        except (urllib.error.URLError,TimeoutError,ValueError,OSError):
            print("PIN_OAUTH_"+name+"_UNAVAILABLE=1",flush=True)
    return 0

if __name__=="__main__":
    try:
        sys.exit(probe())
    except (RuntimeError, ValueError, json.JSONDecodeError):
        print("PIN_BWS_INVENTORY_UNAVAILABLE=1",flush=True)
        sys.exit(2)
