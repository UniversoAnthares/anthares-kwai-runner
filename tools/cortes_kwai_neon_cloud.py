#!/usr/bin/env python3
"""Canonical Kwai/Neon publication queue client for GitHub-hosted Android.

OIDC is bound to the cortes-kwai-cloud-publisher.yml workflow on main.
No alternative Cloudflare job authority or Windows fallback. All writes are
single-shot: ambiguous responses are never replayed. A pre-start failure
retains the job in queued; a post-start failure becomes uncertain.
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API="https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/"
AUD="https://anthares-remote-primary.vercel.app/api/cortes-queue"
TARGET="kwai:lucasrosalem"
ACTIONS={"status":"kwai-uncertain-read","lease":"kwai-lease","renew":"kwai-renew",
         "start":"kwai-start","confirm":"kwai-confirm","fail":"kwai-fail"}
OWNER="kwai-cloud:cortes-kwai-cloud-publisher.yml"

class QueueError(Exception):
    pass

def oidc():
    import urllib.parse
    url=os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL","")
    secret=os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not url or not secret or os.getenv("GITHUB_REPOSITORY")!="UniversoAnthares/anthares-kwai-runner" or os.getenv("GITHUB_REF")!="refs/heads/main" or os.getenv("GITHUB_ACTIONS")!="true":
        raise QueueError("KWAI_NEON_OIDC_CONTEXT_REQUIRED")
    sep="&" if "?" in url else "?"
    req=Request(url+sep+urlencode({"audience":AUD}),headers={"Authorization":"bearer "+secret})
    with urlopen(req,timeout=15) as res:
        token=json.load(res)["value"]
    if not isinstance(token,str) or len(token)<60:
        raise QueueError("KWAI_NEON_OIDC_INVALID")
    return token

def request(action, payload):
    if action not in ACTIONS:
        raise QueueError("KWAI_NEON_ACTION_INVALID")
    payload={"target_key":TARGET,"expected_account":"lucasrosalem",**payload}
    if payload.get("target_key")!=TARGET or payload.get("expected_account")!="lucasrosalem":
        raise QueueError("KWAI_NEON_WRONG_TARGET")
    data=json.dumps(payload,separators=(",",":"),sort_keys=True).encode()
    req=Request(API+"?"+urlencode({"action":ACTIONS[action]}),data=data,method="POST",headers={
      "Authorization":"Bearer "+oidc(),"Content-Type":"application/json","Accept":"application/json"})
    # A transport failure may follow a committed mutation. Never retry.
    try:
        with urlopen(req,timeout=30) as res:
            response=json.load(res)
    except HTTPError as exc:
        raise QueueError("KWAI_NEON_HTTP_"+str(exc.code)) from None
    except (URLError,TimeoutError,OSError,ValueError):
        raise QueueError("KWAI_NEON_OUTCOME_UNKNOWN_STOP") from None
    if response.get("ok") is not True:
        raise QueueError("KWAI_NEON_"+str(response.get("error","REJECTED"))[:80])
    return response

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("action",choices=tuple(ACTIONS))
    ap.add_argument("--json",default="{}")
    args=ap.parse_args()
    body=json.loads(open(args.json[1:],encoding="utf8").read()) if args.json.startswith("@") else json.loads(args.json)
    if not isinstance(body,dict):
        raise QueueError("KWAI_NEON_INPUT_OBJECT_REQUIRED")
    if args.action in {"renew","start","confirm","fail"}:
        job=str(body.get("id") or "")
        fence=body.get("lease_generation")
        if not re.fullmatch(r"kwai-cortes-[A-Za-z0-9._:-]{3,145}",job) or not isinstance(fence,int) or fence<1:
            raise QueueError("KWAI_NEON_FENCE_INVALID")
    if args.action=="confirm":
        proof=body.get("confirmation_evidence")
        if not isinstance(proof,dict) or not proof.get("attestation_hmac") or not body.get("remote_id"):
            raise QueueError("KWAI_NEON_INDEPENDENT_CONFIRMATION_MISSING")
    outcome=request(args.action,body)
    if args.action=="status":
        print("KWAI_NEON_STATUS=READ_ONLY")
        print("KWAI_NEON_UNCERTAIN="+str(len(outcome.get("records",[]))))
        print("KWAI_NEON_ELIGIBLE="+str(outcome.get("eligible_count",0)))
        print("KWAI_NEON_UNCERTAIN_GATE="+str(outcome.get("status","UNKNOWN")))
    elif args.action=="lease":
        job=outcome.get("job")
        if job is None:
            print("KWAI_NEON_LEASE=NONE")
            print("KWAI_NEON_PUBLICATION_ATTEMPTED=0")
        else:
            print("KWAI_NEON_LEASE=ACQUIRED")
            # Use file with restricted permissions; never echo callback tokens.
            dest=os.getenv("KWAI_NEON_LEASE_FILE","kwai-neon-lease.json")
            from pathlib import Path
            path=Path(dest)
            if path.exists():
                raise QueueError("KWAI_NEON_EXISTING_LEASE_RECEIPT")
            path.write_text(json.dumps(job,separators=(",",":")),encoding="utf8")
            path.chmod(0o600)
            print("KWAI_NEON_LEASE_GEN="+str(job.get("lease_generation","")))
    else:
        print("KWAI_NEON_"+args.action.upper()+"=ACK")
        print("KWAI_NEON_FENCE="+str(body["lease_generation"]))
    return 0

if __name__=="__main__":
    try:
        sys.exit(main())
    except (QueueError,ValueError,KeyError) as exc:
        print(str(exc).splitlines()[0][:160],file=sys.stderr)
        sys.exit(89)
