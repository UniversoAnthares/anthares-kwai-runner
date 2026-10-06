#!/usr/bin/env python3
# Executable model of the safety contract around the irreversible boundary.
import sys
case=sys.argv[1]; calls=[]; state="PENDING"; started=False
def started_ack(ok=True):
 global state,started
 calls.append("started")
 if ok: state="PUBLISH_REQUESTED"; started=True; return True
 return False
def commit(crash=False):
 global state
 assert started
 calls.append("commit")
 if crash: state="UNCERTAIN"; raise RuntimeError("crash-after-irreversible-boundary")
 state="PUBLISH_REQUESTED"
def restart():
 global state
 calls.append("restart")
 # UNCERTAIN is observation-only; publication functions are forbidden.
 if state=="UNCERTAIN": calls.append("reconcile-observe"); return
 calls.append("prepare")
try:
 if case=="crash-immediate":
  started_ack(); commit(True)
 elif case=="crash-before-started":
  if not started_ack(False): state="PENDING"
 elif case=="restart-uncertain":
  state="UNCERTAIN"; restart()
 elif case=="double-restart":
  state="UNCERTAIN"; restart(); restart()
 elif case=="uncertain-positive-reconcile":
  state="UNCERTAIN"; restart(); calls.append("confirm-specific"); state="CONFIRMED"
 else: raise SystemExit(2)
except RuntimeError:
 restart()
bad=any(x in calls for x in ["prepare","publish"]) or calls.count("commit")>1
expect={
 "crash-immediate":("UNCERTAIN",["started","commit","restart","reconcile-observe"]),
 "crash-before-started":("PENDING",["started"]),
 "restart-uncertain":("UNCERTAIN",["restart","reconcile-observe"]),
 "double-restart":("UNCERTAIN",["restart","reconcile-observe","restart","reconcile-observe"]),
 "uncertain-positive-reconcile":("CONFIRMED",["restart","reconcile-observe","confirm-specific"])
}[case]
ok=not bad and state==expect[0] and calls==expect[1]
print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"),"STATE="+state,"CALLS="+",".join(calls))
raise SystemExit(0 if ok else 1)
