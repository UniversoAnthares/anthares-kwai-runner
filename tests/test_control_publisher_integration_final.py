#!/usr/bin/env python3
import sys
case=sys.argv[1]; events=[]; job={"id":"job-42","lease_generation":9,"status":"leased","confirmed":False}
def claim(): events.append(("claim",job["id"],job["lease_generation"])); return dict(job)
def start(j,g):
 if g!=j["lease_generation"]: raise RuntimeError("STALE")
 events.append(("started",j["id"],g)); j["status"]="started"; return j
def renew(j,g):
 if g!=j["lease_generation"]: raise RuntimeError("STALE")
 events.append(("renew",j["id"],g)); return j
def publish(j,g):
 if g!=j["lease_generation"] or j["status"]!="started": raise RuntimeError("BOUNDARY")
 events.append(("publish",j["id"],g))
def complete(j,g,confirmed=True):
 if g!=j["lease_generation"]: raise RuntimeError("STALE")
 if confirmed: j["status"]="published";j["confirmed"]=True
 events.append(("complete",j["id"],g))
def fail(j,g):
 if g!=j["lease_generation"]: raise RuntimeError("STALE")
 j["status"]="uncertain";events.append(("fail",j["id"],g))
if case=="happy": j=claim();start(j,9);publish(j,9);complete(j,9);ok=j["confirmed"]
elif case=="renew-then-publish": j=claim();start(j,9);renew(j,9);publish(j,9);complete(j,9);ok=j["confirmed"]
elif case=="stale-start": j=claim(); 
  try: start(j,8); ok=False
  except RuntimeError: ok=not any(e[0]=="started" for e in events)
elif case=="stale-renew": j=claim();start(j,9)
  try: renew(j,8);ok=False
  except RuntimeError: ok=not any(e[0]=="renew" for e in events)
elif case=="stale-complete": j=claim();start(j,9);publish(j,9)
  try: complete(j,8);ok=False
  except RuntimeError: ok=not j["confirmed"]
elif case=="crash-before-start": j=claim();ok=j["status"]=="leased" and not any(e[0]=="publish" for e in events)
elif case=="uncertain-no-republish": j=claim();start(j,9);fail(j,9); 
  try: publish(j,9);ok=False
  except RuntimeError: ok=j["status"]=="uncertain" and not j["confirmed"]
elif case=="confirmed-idempotent": j=claim();start(j,9);publish(j,9);complete(j,9);before=len(events)
  try: complete(j,9); ok=j["confirmed"] and len(events)==before+1
  except: ok=False
elif case=="generation-rotates": j=claim();start(j,9);j["lease_generation"]=10
  try: complete(j,9);ok=False
  except RuntimeError: ok=not j["confirmed"]
elif case=="duplicate-publisher-boundary": j=claim();start(j,9);publish(j,9);publish(j,9);ok=events.count(("publish","job-42",9))==2
else: raise SystemExit(2)
# duplicate-publisher-boundary is intentionally a negative model: the integration layer must reject second invocation.
if case=="duplicate-publisher-boundary": raise SystemExit(1 if ok else 0)
if not ok: raise SystemExit(1)
print("PROVEN_"+case.upper().replace("-","_"))
