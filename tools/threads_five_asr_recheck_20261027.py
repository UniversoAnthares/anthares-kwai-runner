#!/usr/bin/env python3
"""One-shot checksum-pinned recheck of one noisy clip. No publishing or Neon mutations."""
import base64, hashlib, json, os, re, tempfile, urllib.parse, urllib.request
from pathlib import Path
from faster_whisper import WhisperModel

SOURCE = "fOmihuHUT1M"
START = int(os.environ["ASR_START"])
HOLDS = {1325, 2182, 4762, 7788, 11060}
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"Anthares-ASR-Quality-Recheck/1.0"}),timeout=90)
def variation(excerpt):
    tokens=re.findall(r"\w+",excerpt.lower())
    if not tokens:return {"dominant":1.0,"distinct":0.0}
    freq={x:tokens.count(x) for x in set(tokens)}
    return {"dominant":round(max(freq.values())/len(tokens),4),"distinct":round(len(freq)/len(tokens),4)}
def transcribe(model,media):
    segments,_info=model.transcribe(media,language="pt",beam_size=5,temperature=0,condition_on_previous_text=False,vad_filter=True,vad_parameters={"min_silence_duration_ms":400})
    cues=[{"start":round(float(s.start),2),"end":round(float(s.end),2),"text":s.text.strip()} for s in segments if s.text.strip() and s.end>s.start]
    excerpt=" ".join(x["text"] for x in cues)
    return {"cues":cues,"excerpt":excerpt,"metrics":variation(excerpt)}
def main():
    if START not in HOLDS:raise RuntimeError("NOT_IN_ALLOWED_RECHECK_SET")
    manifest=json.loads((Path(__file__).resolve().parents[1]/"config/threads-asr-batch-20261027.json").read_text("utf8"))
    row=next(x for x in manifest["entries"] if x["start"]==START)
    clip=row["clip_id"];uri=row["url"]
    required=f"https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_{SOURCE}_g1_{row['start']}_{row['end']}.mp4"
    if uri!=required:raise RuntimeError("URL_NOT_PINNED")
    q=urllib.parse.urlencode({"search":uri.rsplit("/",1)[1].removesuffix(".mp4"),"per_page":"30"})
    with fetch("https://anthares.us/wp-json/wp/v2/media?"+q) as response:media=json.load(response)
    matches=[m for m in media if m.get("source_url")==uri and m.get("mime_type")=="video/mp4"]
    if len(matches)!=1:raise RuntimeError("WP_ATTACHMENT_NOT_UNIQUE")
    with tempfile.TemporaryDirectory(prefix="anthares-five-asr-") as directory:
        path=Path(directory)/"source.mp4";digest=hashlib.sha256();size=0
        with fetch(uri) as response,path.open("wb") as out:
            while block:=response.read(1024*1024):
                digest.update(block);size+=len(block)
                if size>70_000_000:raise RuntimeError("MEDIA_TOO_LARGE")
                out.write(block)
        if digest.hexdigest()!=row["sha"]:raise RuntimeError("SHA_MISMATCH")
        small=transcribe(WhisperModel("small",device="cpu",compute_type="int8",cpu_threads=4),str(path))
        medium=transcribe(WhisperModel("medium",device="cpu",compute_type="int8",cpu_threads=4),str(path))
        evidence={"clip_id":clip,"attachment_id":int(matches[0]["id"]),"sha256":row["sha"],"bytes":size,"small":small,"medium":medium}
        outdir=Path(os.environ["RUNNER_TEMP"])/"anthares-asr-five";outdir.mkdir(parents=True,exist_ok=True)
        (outdir/(str(START)+".json")).write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n","utf8")
        encoded=base64.b64encode(json.dumps(evidence,ensure_ascii=False,separators=(",",":")).encode()).decode()
        print(f"ASR_RECHECK_PROOF start={START} attachment={evidence['attachment_id']} sha={row['sha']} small_words={len(small['excerpt'].split())} small_dominant={small['metrics']['dominant']} medium_words={len(medium['excerpt'].split())} medium_dominant={medium['metrics']['dominant']}",flush=True)
        print("ASR_RECHECK_BASE64="+encoded,flush=True)
if __name__=="__main__":main()
