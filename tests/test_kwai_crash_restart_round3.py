#!/usr/bin/env python3
import sys
case=sys.argv[1]; state="UNCERTAIN"; calls=[]
if case=="late-complete-ack": calls+=["restart","reconcile-observe","late-complete-ignored"]
elif case=="old-generation-restart": calls+=["restart","old-generation-denied","reconcile-observe"]
elif case=="new-generation-claim": calls+=["restart","new-claim-denied","reconcile-observe"]
elif case=="three-restarts": calls+=["restart","reconcile-observe"]*3
elif case=="positive-then-restart": calls+=["reconcile-observe","specific-positive"]; state="CONFIRMED"; calls+=["restart","already-confirmed-no-publish"]
else: raise SystemExit(2)
bad=any(x in calls for x in ["prepare","commit","publish","claim-accepted"])
ok=not bad and state in ("UNCERTAIN","CONFIRMED")
print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"),state,",".join(calls));raise SystemExit(0 if ok else 1)
