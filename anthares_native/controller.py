#!/usr/bin/env python3
"""Independent state controller. Does not infer login or publication from CI success."""
import argparse
import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class Stage(str, Enum):
    BOOTSTRAP="bootstrap"
    NEEDS_AUTH="needs_auth"
    AUTHENTICATED="authenticated"
    SESSION_PERSISTED="session_persisted"
    PUBLISHING="publishing"
    PUBLISHED="published"

@dataclass(frozen=True)
class Evidence:
    identity_verified: bool=False
    encrypted_session_saved: bool=False
    restored_identity_verified: bool=False
    video_url: str=""
    publication_verified: bool=False

def advance(current: Stage, evidence: Evidence) -> Stage:
    if evidence.publication_verified and evidence.video_url.startswith("https://") and evidence.restored_identity_verified:
        return Stage.PUBLISHED
    if evidence.restored_identity_verified and evidence.encrypted_session_saved:
        return Stage.SESSION_PERSISTED
    if evidence.identity_verified:
        return Stage.AUTHENTICATED
    return Stage.NEEDS_AUTH

def report(evidence: Evidence):
    state=advance(Stage.BOOTSTRAP,evidence)
    return {
        "schema":"anthares.native.control.v1",
        "stage":state.value,
        "identity_verified":evidence.identity_verified,
        "persistent_session_verified":evidence.restored_identity_verified and evidence.encrypted_session_saved,
        "publication_verified":state==Stage.PUBLISHED,
        "next_action":{
            Stage.NEEDS_AUTH:"establish_real_identity",
            Stage.AUTHENTICATED:"persist_and_restore_encrypted_session",
            Stage.SESSION_PERSISTED:"publish_and_verify_public_video",
            Stage.PUBLISHED:"advance_queue",
        }[state],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--evidence",required=True)
    p.add_argument("--output",default="anthares-native-status.json")
    a=p.parse_args()
    raw=json.loads(Path(a.evidence).read_text())
    permitted={k:raw[k] for k in Evidence.__dataclass_fields__ if k in raw}
    result=report(Evidence(**permitted))
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("ANTHARES_NATIVE_STAGE="+result["stage"])
    print("ANTHARES_NATIVE_NEXT="+result["next_action"])

if __name__=="__main__":
    main()
