#!/usr/bin/env python3
"""Fail-closed contract helpers for the authenticated Kwai Studio web route.

This module deliberately handles only non-secret UI observations. It never reads,
serializes or exports browser cookies, tokens or storage.
"""
from __future__ import annotations
import json, os, sys, time

LOGIN_MARKERS=("faça login","fazer login","log in","login","verification code","código de verificação")
AUTH_MARKERS=("criar tráfego","criar trafego","operar","cancelar","kwai studio")
SUBMIT_MARKERS=("publicar","publish","post","enviar")

def classify_ui(text:str)->str:
    t=" ".join((text or "").casefold().split())
    if any(x in t for x in LOGIN_MARKERS):
        return "LOGIN_REQUIRED"
    if "kwai studio" in t and any(x in t for x in AUTH_MARKERS):
        return "AUTHENTICATED"
    return "UNKNOWN"

def require_ready(observation:dict)->None:
    if classify_ui(str(observation.get("ui_text","")))!="AUTHENTICATED":
        raise SystemExit("KWAI_STUDIO_NOT_AUTHENTICATED")
    expected=os.getenv("KWAI_EXPECTED_ACCOUNT","").strip()
    observed=str(observation.get("account","")).strip()
    if expected and observed!=expected:
        raise SystemExit("KWAI_STUDIO_ACCOUNT_MISMATCH")
    ts=float(observation.get("observed_at",0))
    if abs(time.time()-ts)>int(os.getenv("KWAI_STUDIO_OBSERVATION_MAX_AGE","300")):
        raise SystemExit("KWAI_STUDIO_OBSERVATION_STALE")

def require_commit_proof(proof:dict)->None:
    required=("job_id","lease_generation","publication_started_ack","media_sha256")
    if any(not str(proof.get(k,"")).strip() for k in required):
        raise SystemExit("KWAI_STUDIO_COMMIT_PROOF_INCOMPLETE")
    if proof.get("publication_started_ack") is not True:
        raise SystemExit("KWAI_STUDIO_COMMIT_NOT_ACKED")

def main()->int:
    phase=(sys.argv[1] if len(sys.argv)>1 else "").strip().lower()
    if phase not in ("classify","prepare","commit"):
        raise SystemExit("usage: kwai_studio_web_publish.py classify|prepare|commit")
    raw=sys.stdin.read().strip()
    data=json.loads(raw or "{}")
    if phase=="classify":
        print("STATE="+classify_ui(str(data.get("ui_text",""))))
        return 0
    require_ready(data.get("observation",{}))
    media=data.get("media",{})
    if not media.get("sha256") or not media.get("path"):
        raise SystemExit("KWAI_STUDIO_MEDIA_IDENTITY_MISSING")
    if phase=="prepare":
        print("STATE=READY_TO_PREPARE_WEB_UPLOAD")
        print("IRREVERSIBLE_SUBMIT=BLOCKED")
        return 0
    require_commit_proof(data.get("commit_proof",{}))
    if data["commit_proof"]["media_sha256"]!=media["sha256"]:
        raise SystemExit("KWAI_STUDIO_MEDIA_PROOF_MISMATCH")
    print("STATE=COMMIT_AUTHORIZED")
    print("NOTE=browser-driver-must-click-exactly-once-and-return-UNCERTAIN-on-ambiguous-result")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
