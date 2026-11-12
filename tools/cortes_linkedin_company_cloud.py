#!/usr/bin/env python3
"""Official LinkedIn organization CORTES publisher; no Buffer.

GitHub OIDC authenticates a separate Neon fenced queue role. Only a signed,
provider-confirmed remote publication is marked CONFIRMED; ambiguous posts stay
UNCERTAIN and are never uploaded twice.
"""
from __future__ import annotations
import json
import os
import re
import sys
import urllib.parse
import urllib.request

from tools.cortes_queue_ha import post
from tools.cortes_social_queue_consumer import _safe_job
from tools.cortes_social_media_probe import available as media_available
from tools.cortes_linkedin_personal_cloud import public_embed_status
from social_adapters.video_social import linkedin, ConfigRequired, PlatformLimit

OWNER = "linkedin-company:github-cloud-v1"
TARGET = "linkedin:primary"
AUDIENCE = "https://anthares-remote-primary.vercel.app/api/cortes-queue"
WORKFLOW = "cortes-linkedin-company-direct-cloud.yml"
COMPANY = "urn:li:organization:145345334"

def cloud_only():
    checks = (
      os.getenv("GITHUB_ACTIONS") == "true",
      os.getenv("RUNNER_ENVIRONMENT") == "github-hosted",
      os.getenv("RUNNER_OS") == "Linux",
      os.getenv("GITHUB_REPOSITORY") == "UniversoAnthares/anthares-kwai-runner",
      os.getenv("GITHUB_REF") == "refs/heads/main",
      os.getenv("GITHUB_WORKFLOW_REF", "").endswith("/.github/workflows/" + WORKFLOW + "@refs/heads/main"),
      os.getenv("ANTHARES_SOCIAL_COMMIT") == "1",
      bool(os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL") and os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN")),
    )
    if not all(checks):
        raise ConfigRequired("LINKEDIN_COMPANY_HOSTED_WORKFLOW_ONLY")
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not token or any(x in token for x in "\r\n\x00"):
        raise ConfigRequired("LINKEDIN_COMPANY_ACCESS_TOKEN_UNAVAILABLE")
    if os.getenv("LINKEDIN_AUTHOR_URN") != COMPANY:
        raise ConfigRequired("LINKEDIN_COMPANY_AUTHOR_URN_INVALID")
    os.environ["CORTES_QUEUE_PRIMARY"] = "neon"

def authorize_company_admin():
    """Verify this OAuth subject administers the pinned organization before Neon lease.

    A member token alone grants no organization publication. Permission checks
    are read-only and fail closed; neither body nor subject is ever logged.
    """
    token=os.environ["LINKEDIN_ACCESS_TOKEN"].strip()
    endpoint=("https://api.linkedin.com/v2/organizationalEntityAcls?"
              "q=roleAssignee&role=ADMINISTRATOR&state=APPROVED&count=100")
    request=urllib.request.Request(endpoint, method="GET", headers={
        "Authorization":"Bearer "+token,
        "X-Restli-Protocol-Version":"2.0.0",
        "Accept":"application/json",
    })
    try:
        with urllib.request.urlopen(request,timeout=22) as response:
            doc=json.load(response)
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,
            ValueError,OSError) as exc:
        raise ConfigRequired("LINKEDIN_COMPANY_ADMIN_READ_AUTH_REQUIRED") from None
    if not isinstance(doc,dict) or not isinstance(doc.get("elements"),list):
        raise ConfigRequired("LINKEDIN_COMPANY_ADMIN_RESPONSE_INVALID")
    for entry in doc["elements"]:
        if not isinstance(entry,dict):
            continue
        if entry.get("role")!="ADMINISTRATOR" or entry.get("state")!="APPROVED":
            continue
        target=str(entry.get("organization") or entry.get("organizationalTarget") or "")
        if target==COMPANY:
            print("LINKEDIN_COMPANY_PINNED_ADMIN_VERIFIED=1",flush=True)
            return
    raise ConfigRequired("LINKEDIN_COMPANY_ACCOUNT_ADMIN_NOT_VERIFIED")


def oidc():
    url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"audience": AUDIENCE})
    req = urllib.request.Request(url,headers={
      "Authorization": "Bearer "+os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"],
      "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=15) as response:
        return json.load(response)["value"]

def queue(action, data=None):
    result=post("company-"+action,data or {},oidc)
    if not result.get("ok"):
        raise RuntimeError("COMPANY_QUEUE_"+action.upper()+"_REJECTED")
    return result

def reconcile():
    control=public_embed_status("urn:li:ugcPost:0000000000000000000")
    if control != 404:
        return 0
    matched=0
    for job in queue("pending").get("jobs") or []:
        remote=str(job.get("remote_id") or "")
        if public_embed_status(remote)==200:
            try:
                queue("reconcile-public",{"id":job["id"],"remote_id":remote,
                     "public_status":200,"control_status":404,
                     "proof_kind":"linkedin_public_embed_head"})
                matched+=1
            except (RuntimeError,KeyError):
                pass
    return matched

def publish_one():
    result=queue("lease",{"target_key":TARGET,"owner":OWNER})
    job=result.get("job")
    if not job:
        return {"linkedin_company":"IDLE","limit":bool(result.get("daily_limit_reached"))}
    fence={"id":job["id"],"owner":OWNER,"lease_generation":job["lease_generation"]}
    started=False
    try:
        raw=job.get("payload") or {}
        if isinstance(raw,str):
            raw=json.loads(raw)
        job={**job,"payload":raw}
        payload=_safe_job(job,"linkedin","primary")
        if payload.get("account_id")!="primary":
            raise RuntimeError("COMPANY_PAYLOAD_ACCOUNT_DENIED")
        if linkedin(payload,publish=False).get("status")!="READY":
            raise RuntimeError("COMPANY_METADATA_INVALID")
        if not media_available(payload["media_url"]):
            queue("media-missing",fence)
            return {"linkedin_company":"SOURCE_MEDIA_QUARANTINED"}
        queue("start",fence)
        started=True
        pub=linkedin(payload,publish=True)
        remote=str(pub.get("remote_id") or "")
        proof=pub.get("confirmation_evidence") or {}
        if pub.get("status")=="CONFIRMED" and remote and (
           proof.get("kind")=="linkedin_author_readback_verified"
           and proof.get("verified_id")==remote and proof.get("author_verified") is True):
            queue("confirmed",{**fence,"remote_id":remote,"confirmation_evidence":proof})
            return {"linkedin_company":"CONFIRMED","remote_id":remote}
        if pub.get("status")=="ACCEPTED_UNVERIFIED" and remote:
            queue("accepted",{**fence,"remote_id":remote})
            return {"linkedin_company":"ACCEPTED_PENDING_PUBLIC_READBACK"}
        raise RuntimeError("COMPANY_POST_UNVERIFIED")
    except Exception:
        try:
            queue("fail",fence)
        except Exception:
            pass
        return {"linkedin_company":"HELD_UNCERTAIN" if started else "BLOCKED_BEFORE_SUBMIT"}

def main():
    try:
        cloud_only()
        authorize_company_admin()
        try:
            n=reconcile()
        except Exception:
            n=0
        print("LINKEDIN_COMPANY_PUBLIC_RECONCILED="+str(n),flush=True)
        out=publish_one()
        print(json.dumps(out,separators=(",",":")),flush=True)
        return 0 if out.get("linkedin_company") not in {"BLOCKED_BEFORE_SUBMIT","HELD_UNCERTAIN"} else 2
    except (ConfigRequired,PlatformLimit) as exc:
        print("LINKEDIN_COMPANY_UNAVAILABLE="+type(exc).__name__,flush=True)
        return 2
    except Exception as exc:
        print("LINKEDIN_COMPANY_BLOCKED="+type(exc).__name__,flush=True)
        return 2

if __name__=="__main__":
    sys.exit(main())
