#!/usr/bin/env python3
"""Promote ONE already scheduled, Neon-ledger-backed Pinterest Buffer post.

Never creates a new post. Verifies exact Buffer channel, Pinterest board and
automatic scheduling before an irreversible editPost(mode:shareNow). A lost
mutation response is UNCERTAIN and is NEVER retried by this script.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from social_adapters.buffer_three_channels import api,BufferBlocked,PINNED_CHANNELS,PINTEREST_PUBLIC_BOARD_ID

PINNED_ID="6ad908b1c2fd6c7a0efc0f97"
CHANNEL=PINNED_CHANNELS["pinterest"][0]
EXPECTED_BOARD=PINTEREST_PUBLIC_BOARD_ID

def read_post():
    q=('query CortesPinPromoteReadback { post(input: { id: '
       +json.dumps(PINNED_ID)+
       ' }) { id status channelId channelService schedulingType externalLink dueAt '
       'metadata { ... on PinterestPostMetadata { board { serviceId } } } } }')
    last=None
    for i in range(3):
        try:
            row=api(q).get("post") or {}
            if str(row.get("id") or "")!=PINNED_ID:
                raise RuntimeError("BUFFER_PIN_ID_MISMATCH")
            return row
        except BufferBlocked as exc:
            last=exc
            if i<2:time.sleep(i+1)
    raise RuntimeError("BUFFER_PIN_READBACK_UNAVAILABLE") from last

def verify_link(link):
    uri=urllib.parse.urlparse(str(link or ""))
    return (uri.scheme=="https" and uri.hostname in ("pinterest.com","www.pinterest.com","br.pinterest.com")
            and re.fullmatch(r"/pin/[0-9]+/?",uri.path) is not None)

def main():
    if os.getenv("GITHUB_ACTIONS")!="true" or os.getenv("RUNNER_ENVIRONMENT")!="github-hosted" or os.getenv("RUNNER_OS")!="Linux":
        raise RuntimeError("PINTEREST_PROMOTE_CLOUD_ONLY")
    if not os.getenv("BUFFER_API_KEY"):raise RuntimeError("BUFFER_SECRET_MISSING")
    row=read_post()
    if row.get("channelId")!=CHANNEL or str(row.get("channelService") or "").lower()!="pinterest":
        raise RuntimeError("BUFFER_PIN_IDENTITY_UNVERIFIED")
    if str(row.get("schedulingType") or "").lower()!="automatic":
        raise RuntimeError("PINTEREST_PIN_NOT_AUTO_PUBLISHABLE")
    status=str(row.get("status") or "").lower()
    print("PIN_EXISTING_STATUS="+status,flush=True)
    if status=="sent":
        if not verify_link(row.get("externalLink")):raise RuntimeError("PINTEREST_SENT_LINK_INVALID")
        print("PIN_ALREADY_SENT_URL="+str(row["externalLink"]),flush=True)
        return 0
    if status!="buffer":
        raise RuntimeError("PINTEREST_PIN_NOT_BUFFERED")
    board=str(((row.get("metadata") or {}).get("board") or {}).get("serviceId") or "")
    if board!=EXPECTED_BOARD:
        raise RuntimeError("PINTEREST_EXISTING_PIN_BOARD_UNVERIFIED")
    print("PIN_EXISTING_BOARD_VERIFIED=1",flush=True)
    mutation=('mutation CortesPromoteExistingPinterestPin { editPost(input: { id: '
              +json.dumps(PINNED_ID)+', mode: shareNow }) { '
              '... on PostActionSuccess { post { id status channelId schedulingType externalLink } } '
              '... on MutationError { message } } }')
    # Exactly ONE mutation; any 5xx/timeout yields UNCERTAIN, no automatic retry.
    try:
        edited=api(mutation).get("editPost") or {}
    except BufferBlocked as exc:
        print("::error::PINTEREST_PROMOTE_MUTATION_RESULT_UNCERTAIN",flush=True)
        raise RuntimeError("PINTEREST_PROMOTE_MUTATION_RESULT_UNCERTAIN") from exc
    node=edited.get("post") or {}
    if str(node.get("id") or "")!=PINNED_ID or node.get("channelId")!=CHANNEL:
        print("::error::PINTEREST_PROMOTE_EDIT_REJECTED_OR_UNCERTAIN",flush=True)
        raise RuntimeError("PINTEREST_PROMOTE_EDIT_REJECTED_OR_UNCERTAIN")
    print("PIN_PROMOTE_BUFFER_ACKNOWLEDGED=1",flush=True)
    # Read-only post state can be checked repeatedly without retrying the mutation.
    for attempt in range(12):
        try:
            latest=read_post()
        except (RuntimeError,BufferBlocked):
            time.sleep(5)
            continue
        if str(latest.get("status") or "").lower()=="sent" and verify_link(latest.get("externalLink")):
            print("PIN_PUBLIC_LINK="+str(latest["externalLink"]),flush=True)
            return 0
        if str(latest.get("status") or "").lower() in ("failed","error"):
            print("::error::PINTEREST_BUFFER_PUBLISH_FAILED",flush=True)
            return 2
        if attempt<11:time.sleep(5)
    print("PIN_PROMOTED_PENDING_SOCIAL_CONFIRMATION=1",flush=True)
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        print("::error::PINTEREST_FIRST_PIN_PROOF_FAILED kind="+type(exc).__name__,flush=True)
        sys.exit(2)
