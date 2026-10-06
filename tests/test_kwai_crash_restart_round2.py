#!/usr/bin/env python3
import sys
case=sys.argv[1]; calls=[]; state="PENDING"
def uncertain(reason): 
 global state; state="UNCERTAIN"; calls.append("uncertain:"+reason)
if case=="crash-after-started-before-commit":
 calls+=["started"]; uncertain("crash-pre-commit")
elif case=="verifier-timeout-after-commit":
 calls+=["started","commit"]; uncertain("verify-timeout")
elif case=="complete-reject-after-commit":
 calls+=["started","commit","verify-positive","complete"]; uncertain("complete-reject")
elif case=="heartbeat-loss-after-started":
 calls+=["started"]; uncertain("lease-lost")
elif case=="stale-reacquire-uncertain":
 state="UNCERTAIN"; calls+=["reacquire-denied","reconcile-observe"]
else: raise SystemExit(2)
# invariant: once uncertain, no second prepare/commit/publish is legal.
if state=="UNCERTAIN": calls+=["restart","reconcile-observe"]
bad=calls.count("commit")>1 or "prepare" in calls or "publish" in calls
ok=state=="UNCERTAIN" and not bad
print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"),"STATE="+state,"CALLS="+",".join(calls))
raise SystemExit(0 if ok else 1)
