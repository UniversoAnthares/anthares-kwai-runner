"""Fail-closed independent-run Kwai session evidence verifier.

This verifies recorded observations, not Kwai server-side authentication.
No cookies, passwords, screenshots or session tokens are stored.
"""
import argparse
import json
from pathlib import Path

SCHEMA = "anthares.mobile.session-observation.v1"

def validate(observations, account="lucasrosalem"):
    if len(observations) < 2:
        raise ValueError("at least two independent run observations required")
    expected = account.strip().lstrip("@").casefold()
    seen = set()
    fingerprints = set()
    for item in observations:
        if item.get("schema") != SCHEMA:
            raise ValueError("unsupported observation schema")
        run = str(item.get("run_id", "")).strip()
        if not run or run in seen:
            raise ValueError("run IDs must be distinct")
        seen.add(run)
        if item.get("platform") != "kwai":
            raise ValueError("platform mismatch")
        if str(item.get("observed_account", "")).strip().lstrip("@").casefold() != expected:
            raise ValueError("expected account not observed")
        if item.get("profile_visible") is not True or item.get("login_prompt_visible") is not False:
            raise ValueError("authenticated profile not demonstrated")
        if item.get("relaunch_verified") is not True:
            raise ValueError("session did not survive application relaunch")
        if item.get("fresh_runner") is not True:
            raise ValueError("observation not from an independent runner")
        fingerprint = item.get("session_fingerprint")
        if not isinstance(fingerprint, str) or len(fingerprint) < 32:
            raise ValueError("session fingerprint missing or malformed")
        fingerprints.add(fingerprint)
    if len(fingerprints) != 1:
        raise ValueError("session continuity not established")
    return {"independent_runs":len(seen),"account":expected,"ui_session_continuity":True,
            "server_authentication_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("observations",nargs="+",type=Path)
    p.add_argument("--account",default="lucasrosalem")
    args=p.parse_args()
    print(json.dumps(validate([json.loads(p.read_text()) for p in args.observations],args.account),sort_keys=True))

if __name__ == "__main__":
    main()
