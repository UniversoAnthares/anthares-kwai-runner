#!/usr/bin/env python3
"""Fenced evidence-only batch: 149 Neon SHA-pinned clips, 10 items per job.
No Threads API, no Neon writes, no workstation disk. Quota errors stop job immediately.
"""
import base64, hashlib, json, os, re, tempfile, urllib.parse, urllib.request
from pathlib import Path
from faster_whisper import WhisperModel

MANIFEST = Path(__file__).resolve().parents[1] / "config/threads-asr-batch-20261027.json"
OUTDIR = Path(os.environ["RUNNER_TEMP"]) / "anthares-threads-evidence"
BATCH_SIZE = 10
PART = int(os.environ["ANTHARES_BATCH_PART"])
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Anthares-Threads-Batch-ASR/1.0"}),timeout=90)
def run():
    doc = json.loads(MANIFEST.read_text("utf8"))
    assert doc["schema"] == "anthares.asr-batch.2026-10-27.v1"
    entries = doc["entries"]
    if not (0 <= PART * BATCH_SIZE < len(entries)): raise RuntimeError("INVALID_BATCH_PART")
    selected = entries[PART*BATCH_SIZE:(PART+1)*BATCH_SIZE]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    summary=[]
    for e in selected:
        clip=e["clip_id"]
        # Protect integrity; do not trust arbitrary URLs or identities.
        match=re.fullmatch(r"g([0-9]+):([A-Za-z0-9_-]{11}):([0-9]+):([0-9]+)",clip)
        if not match or clip not in e["id"] or e["id"] != "threads:"+e["source"]+"|"+clip: raise RuntimeError("IDENTITY_INVALID")
        if not re.fullmatch(r"[a-f0-9]{64}",e["sha"]): raise RuntimeError("CHECKSUM_INVALID")
        exact = "https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_"+e["source"]+"_g"+match[1]+"_"+match[3]+"_"+match[4]+".mp4"
        if e["url"] != exact: raise RuntimeError("UNTRUSTED_MEDIA_URL")
        # Only the provider's media API is used to establish attachment identity.
        query=urllib.parse.urlencode({"search":exact.split("/")[-1].removesuffix(".mp4"),"per_page":"30"})
        with get("https://anthares.us/wp-json/wp/v2/media?"+query) as response:
            media_rows=json.load(response)
        matches=[m for m in media_rows if m.get("source_url")==exact and m.get("mime_type")=="video/mp4"]
        if len(matches)!=1:
            print("ASR_ITEM_FAILED clip="+clip+" reason=WORDPRESS_ATTACHMENT_NOT_UNIQUE count="+str(len(matches)),flush=True)
            summary.append({"clip":clip,"status":"failed","reason":"WORDPRESS_ATTACHMENT_NOT_UNIQUE"})
            continue
        attachment=int(matches[0]["id"])
        try:
            with tempfile.TemporaryDirectory(prefix="anthares-media-") as tmp:
                location=Path(tmp)/"media.mp4"
                size=0;hash_=hashlib.sha256()
                with get(exact) as response,location.open("wb") as output:
                    while chunk:=response.read(1024*1024):
                        size+=len(chunk)
                        if size>70_000_000: raise RuntimeError("MEDIA_TOO_BIG")
                        hash_.update(chunk);output.write(chunk)
                digest=hash_.hexdigest()
                if digest!=e["sha"] or size<=10000: raise RuntimeError("MEDIA_HASH_MISMATCH")
                segments,_=model.transcribe(str(location),language="pt",beam_size=3,vad_filter=True,condition_on_previous_text=False,temperature=0)
                cues=[{"start":round(float(s.start),2),"end":round(float(s.end),2),"text":s.text.strip()} for s in segments if s.text.strip() and s.end>s.start]
                excerpt=" ".join(c["text"] for c in cues)
                if len(excerpt)<60 or not cues or any(c["end"]>e["end"]-e["start"]+5 for c in cues): raise RuntimeError("ASR_INVALID_OR_SHORT")
                evidence={"schema":"anthares.clip-transcript-attestation.v1","clip_id":clip,"attachment_id":attachment,"source_video_id":e["source"],"source_start_s":e["start"],"source_end_s":e["end"],"media_sha256":digest,"method":"faster-whisper-small-from-media","language":"pt","cues":cues,"excerpt":excerpt,"verified":True}
                clean_name=clip.replace(":","_")+".json"
                (OUTDIR/clean_name).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
                encoded=base64.b64encode(json.dumps(evidence,ensure_ascii=False,separators=(",",":")).encode()).decode()
                print("ASR_VERIFIED clip="+clip+" attachment="+str(attachment)+" sha256="+digest+" bytes="+str(size)+" cues="+str(len(cues))+" chars="+str(len(excerpt)),flush=True)
                print("ASR_EVIDENCE_BASE64="+encoded,flush=True)
                summary.append({"clip":clip,"status":"verified","sha":digest})
        except Exception as exc:
            reason=str(exc).replace("\n"," ")[:120]
            print("ASR_ITEM_FAILED clip="+clip+" reason="+reason,flush=True)
            summary.append({"clip":clip,"status":"failed","reason":reason})
    (OUTDIR/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n","utf8")
    print("ASR_BATCH_DONE part="+str(PART)+" verified="+str(sum(i["status"]=="verified" for i in summary))+" total="+str(len(selected)),flush=True)
if __name__=="__main__":
    run()
