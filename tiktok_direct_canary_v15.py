#!/usr/bin/env python3
import json,os,subprocess,sys,tempfile
from pathlib import Path
import requests

CONTROL=os.environ.get("CONTROL","https://anthares-control.anthares1.workers.dev").rstrip("/")
TOKEN=os.environ["CONTROL_TOKEN"]
JOB_ID="tiktok-canary-20261006-synthetic-v15"
HEAD={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"}

def call(op,payload):
    r=requests.post(CONTROL+"/job/"+op,headers=HEAD,json=payload,timeout=30)
    r.raise_for_status(); return r.json()

def main():
    r=requests.get(CONTROL+"/tiktok/session-state",headers={"Authorization":"Bearer "+TOKEN},timeout=30)
    r.raise_for_status(); d=r.json(); state=d.get("state") or {}
    if d.get("available") is not True or not state.get("cookies"): raise RuntimeError("central session unavailable")
    os.environ["TIKTOK_STORAGE_STATE"]=json.dumps(state,separators=(",",":"))
    print("CENTRAL_SESSION_PROVEN cookies="+str(len(state["cookies"])),flush=True)

    call("enqueue",{"id":JOB_ID,"platform":"tiktok","executor":"github","dedupe_key":JOB_ID,"source_id":"synthetic-owned-canary-v15","source_start":0,"source_end":5})
    lease=None
    for _ in range(60):
        x=call("lease",{"platform":"tiktok","executor":"github","ttl_seconds":900}); j=x.get("job") or {}
        if not j:
            import time
            time.sleep(1)
            continue
        if j.get("id")==JOB_ID: lease=j; break
        if j.get("publication_started"):
            raise RuntimeError("queue blocked by possibly published job "+str(j.get("id")))
        call("fail",{"id":j["id"],"executor":"github","lease_generation":j["lease_generation"],"error_class":"superseded_prepublish_canary","error_message":"safe prepublication retirement","published_possible":False})
    if not lease: raise RuntimeError("exact v15 lease unavailable")
    gen=lease["lease_generation"]; print("EXACT_LEASE_PROVEN generation="+str(gen),flush=True)

    root=Path(tempfile.mkdtemp(prefix="tiktok-v15-")); media=root/"canary.mp4"; plan=root/"plan.json"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","lavfi","-i","color=c=black:s=540x960:r=24:d=5","-f","lavfi","-i","anullsrc=channel_layout=mono:sample_rate=24000","-t","5","-c:v","libx264","-preset","ultrafast","-crf","32","-pix_fmt","yuv420p","-c:a","aac","-b:a","32k",str(media)],check=True)
    plan.write_text(json.dumps({"segment_id":JOB_ID,"source_id":"synthetic-owned-canary-v15","title":"Universo Anthares — teste técnico v15","summary":"Teste técnico controlado.","media_path":str(media)},ensure_ascii=False),encoding="utf-8")

    sys.path.insert(0,str(Path(__file__).resolve().parent/"direct-tiktok-publisher"))
    import tiktok_worker as tw
    tw.STORAGE_RAW=os.environ["TIKTOK_STORAGE_STATE"]
    before=tw.inventory_profile_videos("universo.anthares")
    print("IDENTITY_PROFILE_PREFLIGHT=PROVEN count="+str(len(before)),flush=True)

    call("started",{"id":JOB_ID,"executor":"github","lease_generation":gen})
    print("PUBLICATION_STARTED=1",flush=True)
    os.environ.update({
      "EXPECTED_TIKTOK_USERNAME":"universo.anthares",
      "TIKTOK_YOUTUBE_PLAN":str(plan),
      "ATD_ARTIFACT_DIR":str(root/"artifacts"),
      "TIKTOK_PUBLISHED_KEYS":str(root/"published.json"),
      "TIKTOK_PUBLISH_EVIDENCE":str(root/"evidence.json"),
      "TIKTOK_AUTOMATION_HALT":str(root/"halt.json"),
    })
    try:
        import tiktok_cloud_publish as pub
        pub.PLAN_PATH=plan; pub.ARTIFACT_DIR=root/"artifacts"; pub.PUBLISHED_KEYS_PATH=root/"published.json"; pub.PUBLISH_EVIDENCE_PATH=root/"evidence.json"; pub.HALT_PATH=root/"halt.json"
        pub.main()
        ev=json.loads((root/"evidence.json").read_text(encoding="utf-8")); rid=str(ev.get("remote_id") or "")
        if not rid: raise RuntimeError("publisher returned no independent remote id")
        done=call("complete",{"id":JOB_ID,"executor":"github","lease_generation":gen,"confirmed":True,"remote_id":rid,"confirmation_evidence":"publisher_profile_new_post:"+rid})
        if not (done.get("ok") and (done.get("job") or {}).get("confirmed")): raise RuntimeError("central complete rejected")
        print("TIKTOK_REAL_REMOTE_POST=PROVEN remote_id="+rid,flush=True)
    except Exception as exc:
        try: call("fail",{"id":JOB_ID,"executor":"github","lease_generation":gen,"error_class":"direct_v15_publish_failed","error_message":type(exc).__name__,"published_possible":True})
        except Exception: pass
        print("TIKTOK_V15=UNCERTAIN "+type(exc).__name__,flush=True)
        raise

if __name__=="__main__": main()
