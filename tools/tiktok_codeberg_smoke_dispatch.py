#!/usr/bin/env python3
"""Dispatch only non-publishing Codeberg account/OIDC health checks."""
import base64,json,os,sys,urllib.parse,urllib.request,urllib.error

DEST="https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner/actions/workflows/"
WORKFLOWS=("cortes-tiktok-universo-codeberg.yml","cortes-tiktok-lucas4-codeberg.yml")

def main():
    raw=os.environ.get("CODEBERG_PUSH_URL","")
    target=urllib.parse.urlsplit(raw)
    if (target.scheme!="https" or target.hostname!="codeberg.org"
            or not target.username or not target.password):
        raise RuntimeError("CODEBERG_DISPATCH_AUTH_NOT_BOUND")
    username=urllib.parse.unquote(target.username)
    password=urllib.parse.unquote(target.password)
    auth=base64.b64encode((username+":"+password).encode()).decode()
    credentials={"Authorization":"Basic "+auth,"Accept":"application/json",
                 "Content-Type":"application/json"}
    # Smoke mode cannot trigger publication and requires no special action token.
    body=json.dumps({"ref":"main","inputs":{"smoke":True,"publish":False}}).encode()
    for workflow in WORKFLOWS:
        request=urllib.request.Request(DEST+workflow,data=body,
                                        headers=credentials,method="POST")
        try:
            with urllib.request.urlopen(request,timeout=35) as response:
                if response.status not in (200,201,204):
                    raise RuntimeError("CODEBERG_SMOKE_DISPATCH_UNACKNOWLEDGED")
        except urllib.error.HTTPError as exc:
            # HTTP status is safe diagnostic evidence; never log response body,
            # URL credentials, authorization header or browser cookies.
            print("CODEBERG_TIKTOK_SMOKE_HTTP_"+str(exc.code)+" workflow="+workflow,
                  file=sys.stderr,flush=True)
            raise
        print("CODEBERG_TIKTOK_ACCOUNT_SMOKE_DISPATCHED="+workflow,flush=True)
    print("CODEBERG_TIKTOK_SMOKE_REQUESTS_ACKNOWLEDGED=2",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("::error::CODEBERG_SMOKE_DISPATCH_FAILED="+type(exc).__name__,
              file=sys.stderr,flush=True)
        raise SystemExit(2)
