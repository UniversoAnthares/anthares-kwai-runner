#!/usr/bin/env python3
import argparse,json,os,sys,time,uuid
from pathlib import Path
def stop(reason):
 print(json.dumps({"state":"AUTH_REQUIRED","reason":reason},separators=(",",":")));sys.exit(2)
p=argparse.ArgumentParser();p.add_argument("--account",required=True);p.add_argument("--identity-observed",choices=["true","false"],required=True);p.add_argument("--session-generation",type=int,required=True);p.add_argument("--snapshot",required=True);p.add_argument("--max-snapshot-age",type=int,default=86400);p.add_argument("--out",default="kwai-ready-proof.json");a=p.parse_args()
if a.identity_observed!="true":stop("identity_not_verified")
if a.session_generation<1:stop("invalid_session_generation")
s=Path(a.snapshot)
if not s.is_file() or s.stat().st_size<64:stop("snapshot_missing_or_empty")
age=time.time()-s.stat().st_mtime
if age < -300 or age>a.max_snapshot_age:stop("snapshot_stale")
acct=a.account.strip()
if not acct:stop("account_missing")
expected=os.environ.get("KWAI_EXPECTED_ACCOUNT","").strip()
if expected and acct.casefold()!=expected.casefold():stop("account_mismatch")
proof={"state":"READY","account":acct,"observed_at":int(time.time()),"proof_id":str(uuid.uuid4()),"session_generation":a.session_generation,"snapshot_size":s.stat().st_size}
Path(a.out).write_text(json.dumps(proof,separators=(",",":"))+"\n");os.chmod(a.out,0o600);print(json.dumps(proof,separators=(",",":")))
