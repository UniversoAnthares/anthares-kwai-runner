#!/usr/bin/env python3
"""Read redacted publisher signals, never log or export secrets."""
import argparse
import json
import re
from pathlib import Path

def collect(status: str, publication: str):
    lines=set(x.strip() for x in status.splitlines())
    verified="KWAI_IDENTITY_PROFILE_MATCH=1" in lines and (
        "KWAI_SESSION_AUTHENTICATED" in lines or "KWAI_SESSION_AUTHENTICATED_RESTORED" in lines
    )
    restored=verified and "KWAI_SESSION_AUTHENTICATED_RESTORED" in lines
    session_saved=restored and "KWAI_PRIVATE_VAULT_SAVE_SUCCESS=1" in lines
    pub_lines=set(x.strip() for x in publication.splitlines())
    urls=[x.split("=",1)[1] for x in pub_lines if x.startswith("KWAI_PUBLIC_VIDEO_URL=")]
    url=next((x for x in urls if re.fullmatch(r"https://(?:www[.])?(?:kwai[.]com|kwai-video[.]com)/[^ ]+",x)), "")
    public_ok="KWAI_PUBLICATION_VERIFIED=1" in pub_lines and bool(url)
    return {
        "identity_verified":verified,
        "encrypted_session_saved":session_saved,
        "restored_identity_verified":restored,
        "video_url":url if public_ok else "",
        "publication_verified":public_ok,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--status",required=True)
    p.add_argument("--publication",required=True)
    p.add_argument("--output",default="anthares-native-evidence.json")
    a=p.parse_args()
    evidence=collect(Path(a.status).read_text(),Path(a.publication).read_text())
    Path(a.output).write_text(json.dumps(evidence,sort_keys=True)+"\n")
    print("ANTHARES_NATIVE_EVIDENCE_COLLECTED=1")

if __name__=="__main__":
    main()
