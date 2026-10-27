"""Submit a structured owned quota signal to the Vercel controller.

Call ONLY from inside the exact GitHub Actions run after detecting a confirmed
quota-exhaustion code. Never include job logs, secrets, or arbitrary messages.
"""
from __future__ import annotations
import json, os, sys, urllib.parse, urllib.request

CODES={"ci_quota_exceeded","quota_exceeded","quota_exhausted",
"insufficient_quota","resource_exhausted","billing_hard_limit_reached",
"credits_exhausted","usage_limit_reached","monthly_quota_exceeded",
"daily_quota_exceeded","rate_limit_exceeded"}

def main():
    if len(sys.argv)!=2 or sys.argv[1].strip().lower() not in CODES:
        raise SystemExit("CONFIRMED_STRUCTURED_QUOTA_CODE_REQUIRED")
    token=os.environ.get("GITHUB_TOKEN","")
    repo=os.environ.get("GITHUB_REPOSITORY","")
    run=os.environ.get("GITHUB_RUN_ID","")
    request_url=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    request_token=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    controller=os.environ.get("ANTHARES_CI_QUOTA_CONTROLLER_URL","")
    if not (token and repo and run.isdigit() and request_url and request_token
            and controller.startswith("https://") and controller.endswith("/api/cancel")):
        raise SystemExit("CONTROLLER_IDENTITY_UNAVAILABLE")
    aud="anthares-ci-quota-controller"
    separator="&" if "?" in request_url else "?"
    uri=request_url+separator+urllib.parse.urlencode({"audience":aud})
    with urllib.request.urlopen(urllib.request.Request(uri,headers={
        "Authorization":"Bearer "+request_token
    }),timeout=8) as reply:
        oidc=json.load(reply).get("value","")
    if not oidc: raise SystemExit("OIDC_UNAVAILABLE")
    payload=json.dumps({"repository":repo,"run_id":run,"provider_code":sys.argv[1].strip().lower()}).encode()
    req=urllib.request.Request(controller,data=payload,headers={
        "Authorization":"Bearer "+oidc, "X-GitHub-Actions-Token":token,
        "Content-Type":"application/json"
    },method="POST")
    try:
        with urllib.request.urlopen(req,timeout=20) as reply:
            result=json.load(reply)
    except Exception:
        raise SystemExit("CANCEL_UNCONFIRMED")
    state=str(result.get("state","UNKNOWN"))
    print("QUOTA_OWNED_CANCEL_STATE="+state)
    # Returning nonzero ensures the original job never continues as success.
    raise SystemExit(1)

if __name__=="__main__":
    main()
