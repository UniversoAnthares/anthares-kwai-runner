#!/usr/bin/env python3
"""CORTES queue provider failover, shared Neon ledger, cloud-hosted clients only.

Primary Vercel remains active; Cloudflare HA / two Neon Functions are ready.
Never fail over to work around a 401, 403, 409 or 429. On uncertain network
results, deterministic dedupe IDs and fenced DB operations prevent reposts.
Tokens are never logged.
"""
from __future__ import annotations
import json
import urllib.error
import urllib.parse
import urllib.request

PROVIDERS=(
    "https://anthares-remote-primary.vercel.app/api/cortes-queue",
    "https://anthares-cortes-linkedin-ha.anthares1.workers.dev/",
    "https://br-crimson-unit-b89nau08-corteslinka.compute.c-14.us-east-1.aws.neon.tech/",
    "https://br-crimson-unit-b89nau08-corteslinkb.compute.c-14.us-east-1.aws.neon.tech/",
)
ACTIONS=frozenset({"enqueue","buffer-lease","buffer-start","buffer-fail",
                   "buffer-scheduled","buffer-pending","buffer-reconcile"})


class BackendUnavailable(RuntimeError):
    pass


def post(action: str, payload: dict, get_oidc, *, timeout: int = 14) -> dict:
    if action not in ACTIONS:
        raise ValueError("CORTES_QUEUE_ACTION_NOT_ALLOWED")
    token=get_oidc()
    if not isinstance(token,str) or len(token)<60:
        raise BackendUnavailable("CORTES_QUEUE_OIDC_UNAVAILABLE")
    data=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    if len(data)>131072:
        raise ValueError("CORTES_QUEUE_PAYLOAD_TOO_LARGE")
    for index,provider in enumerate(PROVIDERS):
        target=provider.rstrip("/")+"?"+urllib.parse.urlencode({"action":action})
        request=urllib.request.Request(target,data=data,method="POST",headers={
            "Authorization":"Bearer "+token,"Content-Type":"application/json",
            "Accept":"application/json","User-Agent":"AntharesCortesCloudQueueHA/1.0",
        })
        try:
            with urllib.request.urlopen(request,timeout=timeout) as response:
                result=json.load(response)
            if not isinstance(result,dict):
                raise BackendUnavailable("CORTES_QUEUE_RESPONSE_INVALID")
            return result
        except urllib.error.HTTPError as error:
            if 500<=error.code<=599:
                continue
            # No provider hopping on authorization, platform quota or CAS errors.
            raise BackendUnavailable("CORTES_QUEUE_REJECTED_"+str(error.code)) from None
        except (TimeoutError,urllib.error.URLError,OSError,ValueError):
            continue
    raise BackendUnavailable("CORTES_QUEUE_ALL_PROVIDERS_UNAVAILABLE")
