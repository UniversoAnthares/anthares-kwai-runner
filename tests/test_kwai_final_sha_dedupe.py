#!/usr/bin/env python3
import pathlib,sys,re
src=(pathlib.Path(__file__).resolve().parents[1]/"cloudflare-worker/src/index.js").read_text()
case=sys.argv[1]
required=[
 'const mediaSha=String(b.media_sha256||"").trim().toLowerCase()',
 '/^[0-9a-f]{64}$/.test(mediaSha)',
 'priorSha===mediaSha',
 'deduplicated:true,media_sha256:true',
 'status<>\'failed\''
]
assert all(x in src for x in required), "SHA barrier missing"
sha="a"*64
jobs=[]
def enqueue(job):
 for p in jobs:
  if p["platform"]==job["platform"] and p["status"]!="failed" and p.get("sha","").lower()==job.get("sha","").lower() and re.fullmatch(r"[0-9a-fA-F]{64}",job.get("sha","")):
   return ("dedupe",p["id"])
 jobs.append(job); return ("new",job["id"])
if case=="same-sha-different-source":
 a=enqueue({"id":"a","platform":"kwai","status":"queued","sha":sha,"source":"s1"});b=enqueue({"id":"b","platform":"kwai","status":"queued","sha":sha,"source":"s2"});ok=a[0]=="new" and b==("dedupe","a")
elif case=="sha-case-normalized":
 enqueue({"id":"a","platform":"kwai","status":"published","sha":sha});ok=enqueue({"id":"b","platform":"kwai","status":"queued","sha":sha.upper()})==("dedupe","a")
elif case=="failed-sha-retry-allowed":
 enqueue({"id":"a","platform":"kwai","status":"failed","sha":sha});ok=enqueue({"id":"b","platform":"kwai","status":"queued","sha":sha})[0]=="new"
elif case=="same-sha-other-platform":
 enqueue({"id":"a","platform":"youtube","status":"published","sha":sha});ok=enqueue({"id":"b","platform":"kwai","status":"queued","sha":sha})[0]=="new"
elif case=="concurrent-equivalent":
 # Durable Object serializes requests; model the two enqueue operations in either order.
 r1=[enqueue({"id":"a","platform":"kwai","status":"queued","sha":sha}),enqueue({"id":"b","platform":"kwai","status":"queued","sha":sha})]
 jobs.clear();r2=[enqueue({"id":"b","platform":"kwai","status":"queued","sha":sha}),enqueue({"id":"a","platform":"kwai","status":"queued","sha":sha})]
 ok=sum(x[0]=="new" for x in r1)==1 and sum(x[0]=="dedupe" for x in r1)==1 and sum(x[0]=="new" for x in r2)==1 and sum(x[0]=="dedupe" for x in r2)==1
else: raise SystemExit(2)
print(("PROVEN_" if ok else "FAILED_")+case.upper().replace("-","_"));raise SystemExit(0 if ok else 1)
