#!/usr/bin/env python3
"""One-time, in-memory transfer of account-specific TikTok sessions to Codeberg.

Never export ARA_SHARED to Codeberg. Store only dedicated, minimized TikTok
browser cookies in encrypted Forgejo repository secrets. Service keys are
48-byte independent random values; only their SHA-256 hashes enter log output.
"""
from __future__ import annotations
import base64,hashlib,json,os,secrets,sys,time,urllib.parse,urllib.request,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
from cortes_tiktok_hosted_publish import preflight_vault

DEST="https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner/actions/secrets/"
SUFFIXES={
    "universo.anthares":"UNIVERSO",
    "lucasrosalem4":"LUCAS4"
}

def auth_headers():
    raw=os.environ.get("CODEBERG_PUSH_URL","")
    parsed=urllib.parse.urlsplit(raw)
    if parsed.scheme!="https" or parsed.hostname!="codeberg.org":
        raise RuntimeError("CODEBERG_MIRROR_IDENTITY_UNVERIFIED")
    user=urllib.parse.unquote(parsed.username or "")
    passwd=urllib.parse.unquote(parsed.password or "")
    if not user or not passwd:
        raise RuntimeError("CODEBERG_MIRROR_TOKEN_NOT_BOUND")
    basic=base64.b64encode((user+":"+passwd).encode()).decode()
    return {"Authorization":"Basic "+basic,"Accept":"application/json",
            "Content-Type":"application/json"}

def store(name,value,headers):
    if not value or len(value)>55000:
        raise RuntimeError("CODEBERG_SECRET_SIZE_OR_EMPTY_"+name)
    request=urllib.request.Request(DEST+name,headers=headers,
        data=json.dumps({"data":value}).encode(),method="PUT")
    with urllib.request.urlopen(request,timeout=25) as response:
        if response.status not in (200,201,204):
            raise RuntimeError("CODEBERG_SECRET_ACK_MISSING_"+name)
    print("CODEBERG_ACCOUNT_SECRET_STORED="+name,flush=True)

def auth_cookies(state):
    cookies=state.get("cookies") or []
    selected=[c for c in cookies if str(c.get("domain") or "").endswith("tiktok.com")]
    authentic=[c for c in selected if
       c.get("name") in ("sessionid","sessionid_ss","sid_tt") and
       (not c.get("expires") or float(c["expires"])<0 or float(c["expires"])>time.time())]
    if not authentic:raise RuntimeError("TIKTOK_SESSION_INVALID_OR_EXPIRED")
    return {"cookies":selected,"origins":[]}

def compact(state):
    raw=json.dumps(auth_cookies(state),ensure_ascii=False,separators=(",",":")).encode()
    return base64.b64encode(zlib.compress(raw,9)).decode()

def main():
    if os.environ.get("GITHUB_REF")!="refs/heads/main" or        os.environ.get("EXPECTED_TIKTOK_USERNAME")!="universo.anthares":
        raise RuntimeError("CODEBERG_SECRET_BOOTSTRAP_NONCANONICAL_MAIN")
    headers=auth_headers()
    # Exact primary identity is tested in an isolated Chromium instance.
    primary=preflight_vault()
    if not isinstance(primary,dict):
        raise RuntimeError("PRIMARY_STUDIO_NOT_VERIFIED")
    second_encoded=os.environ.get("TIKTOK_LUCASROSALEM4_STORAGE_STATE","")
    if not second_encoded or len(second_encoded)>55000:
        raise RuntimeError("SECONDARY_STUDIO_SECRET_MISSING")
    try:
        second=json.loads(zlib.decompress(base64.b64decode(second_encoded,validate=True)))
    except (ValueError,zlib.error) as exc:
        raise RuntimeError("SECONDARY_STUDIO_SECRET_INVALID") from exc
    payloads={
        "TIKTOK_UNIVERSO_STORAGE_STATE":compact(primary),
        "TIKTOK_LUCASROSALEM4_STORAGE_STATE":compact(second)
    }
    # Independent keys prevent one compromised account/route affecting another.
    keys={account:base64.urlsafe_b64encode(secrets.token_bytes(48)).decode()
          for account in SUFFIXES}
    for name,value in payloads.items():
        store(name,value,headers)
    for account,suffix in SUFFIXES.items():
        store("CORTES_CODEBERG_TIKTOK_"+suffix+"_KEY",keys[account],headers)
        print("CODEBERG_SERVICE_KEY_HASH account="+account+
              " sha256="+hashlib.sha256(keys[account].encode()).hexdigest(),flush=True)
    print("CODEBERG_TIKTOK_CREDENTIALS_BOOTSTRAPPED=1",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as error:
        # Never print exception messages that may contain URLs, cookies or tokens.
        print("CODEBERG_TIKTOK_BOOTSTRAP_FAILED="+type(error).__name__,file=sys.stderr,flush=True)
        sys.exit(2)
