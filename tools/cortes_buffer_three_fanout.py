#!/usr/bin/env python3
"""CORTES: prioritize first 20 shorts/source in each of 3 Buffer accounts.

The source WordPress master is immutable. Neon is the idempotent queue authority.
Buffer workers refill at most 8 pending slots and later reconcile real posts.
This producer never publishes or marks a post confirmed.
"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import cortes_linkedin_neon_fanout as linked
from anthares_publisher.buffer_distribution import NETWORKS,TARGETS,BUFFER_LIMIT_PER_SOURCE

def per_platform_jobs(jobs, platform):
    if platform not in NETWORKS:
        raise RuntimeError("CORTES_BUFFER_UNKNOWN_PLATFORM")
    target=TARGETS[platform]
    account=target.split(":",1)[1]
    result=[]
    for base in jobs:
        source=base["source_id"]
        segment=base["segment_id"]
        digest=hashlib.sha256((source+"|"+segment+"|"+target).encode()).hexdigest()[:32]
        job_id="cortes-fanout-"+platform+"-"+digest
        copy=dict(base)
        copy.update({"id":job_id,"dedupe_key":job_id,
                     "platform":platform,"account_id":account,"target_key":target})
        result.append(copy)
    return result

def enqueue(job):
    req=urllib.request.Request(linked.NEON+"?action=enqueue",
        data=json.dumps(job,separators=(",",":"),ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Authorization":"Bearer "+linked.oidc(),"Content-Type":"application/json",
                 "User-Agent":"CortesBufferThreeChannelFanout/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=25) as response:
            body=json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("CORTES_BUFFER_FANOUT_HTTP_"+str(exc.code)) from None
    except (urllib.error.URLError,OSError,ValueError):
        raise RuntimeError("CORTES_BUFFER_FANOUT_UNKNOWN_RESPONSE") from None
    row=body.get("job") or {}
    if not body.get("ok") or row.get("id")!=job["id"] or row.get("target_key")!=job["target_key"]:
        raise RuntimeError("CORTES_BUFFER_FANOUT_ACKNOWLEDGEMENT_INVALID")
    if body.get("deduped") and body.get("reason")!="identity":
        raise RuntimeError("CORTES_BUFFER_FANOUT_WRONG_DEDUPE")
    return bool(body.get("deduped"))

def main():
    linked.require_cloud()
    source=linked.wp_state()
    selected=linked.candidate_jobs(source)
    # A fixed 20 per source is a reservation, not 20 simultaneous scheduled posts.
    # Incremental daily reruns safely reuse the same identities.
    counts={}
    for platform in NETWORKS:
        all_jobs=per_platform_jobs(selected,platform)
        budget=50
        windows=max(1,(len(all_jobs)+budget-1)//budget)
        cursor=(int(time.time())//600)%windows
        subset=all_jobs[cursor*budget:(cursor+1)*budget]
        created=known=0
        for job in subset:
            if enqueue(job):known+=1
            else:created+=1
        counts[platform]={"priority_candidates":len(all_jobs),"visited":len(subset),
                          "enqueued":created,"known":known}
        print("CORTES_BUFFER_PRIORITY network="+platform+" created="+str(created)+
              " known="+str(known)+" selected="+str(len(all_jobs)),flush=True)
    print(json.dumps({"ok":True,"priority_per_source":BUFFER_LIMIT_PER_SOURCE,
                     "distribution":counts},separators=(",",":")))

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("::error::CORTES_BUFFER_FANOUT_FAILED="+
              (str(exc) if str(exc).startswith("CORTES_") else type(exc).__name__))
        raise SystemExit(2)
