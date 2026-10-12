#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import x_cloud_prepare as prep

REQ = Path(os.getenv("X_REQUEST_JSON", "x-microcut-request.json"))
PLAN = Path(os.getenv("X_PLAN_JSON", "x-microcut-plan.json"))
WORK = Path(os.getenv("X_CLOUD_WORK", "x-cloud-work"))
OUT = Path(os.getenv("X_RENDER_OUTPUT", "x-cloud-output.mp4"))
FILLERS = {"ah", "ahn", "ha", "ham", "hum", "hmm", "eh", "e", "er", "uh", "uhm"}


def norm(text: str) -> str:
    s = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", s.casefold())


def merge_intervals(rows: list[dict], lo: float, hi: float, max_ratio: float = 0.30) -> list[dict]:
    clean = []
    for row in rows:
        a = max(lo, float(row.get("start", lo)))
        b = min(hi, float(row.get("end", hi)))
        if b - a >= 0.10:
            clean.append({"start": a, "end": b, "reason": str(row.get("reason") or "microcut")[:80]})
    clean.sort(key=lambda x: (x["start"], x["end"]))
    merged = []
    for row in clean:
        if not merged or row["start"] > merged[-1]["end"] + 0.06:
            merged.append({"start": row["start"], "end": row["end"], "reasons": [row["reason"]]})
        else:
            merged[-1]["end"] = max(merged[-1]["end"], row["end"])
            merged[-1]["reasons"].append(row["reason"])
    budget = (hi - lo) * max_ratio
    used = 0.0
    accepted = []
    for row in sorted(merged, key=lambda x: (x["end"] - x["start"], x["start"])):
        span = row["end"] - row["start"]
        if used + span <= budget + 1e-6:
            accepted.append(row)
            used += span
    accepted.sort(key=lambda x: x["start"])
    return accepted


def plan_intervals(req: dict, plan: dict) -> tuple[float, float, list[dict], dict]:
    words = list(req.get("words") or [])
    by_id = {int(w["id"]): w for w in words}
    first = int(plan["start_word_id"])
    last = int(plan["end_word_id"])
    if first not in by_id or last not in by_id or first >= last:
        raise RuntimeError("Plano usa word ids inválidos.")
    lo = float(by_id[first]["s"])
    hi = float(by_id[last]["e"])
    raw_duration = hi - lo
    target = req.get("target_seconds") or {"min":45,"max":90}
    if raw_duration < float(target.get("min",45)) - 1 or raw_duration > float(target.get("max",90)) + 1:
        raise RuntimeError(f"Corte bruto fora da faixa: {raw_duration:.2f}s")

    rows = []
    semantic = list(plan.get("remove") or [])
    for item in semantic:
        if not isinstance(item, dict):
            continue
        try:
            a_id, b_id = int(item["from"]), int(item["to"])
        except Exception:
            continue
        if a_id not in by_id or b_id not in by_id or a_id > b_id:
            continue
        a = float(by_id[a_id]["s"]); b = float(by_id[b_id]["e"])
        if a < lo or b > hi or b - a > 8.0:
            continue
        rows.append({"start":a,"end":b,"reason":str(item.get("reason") or "ai_semantic")})

    selected = [w for w in words if first <= int(w["id"]) <= last]
    for i, w in enumerate(selected):
        dur = float(w["e"]) - float(w["s"])
        tok = norm(w["t"])
        prev_tok = norm(selected[i-1]["t"]) if i else ""
        next_tok = norm(selected[i+1]["t"]) if i+1 < len(selected) else ""
        if tok in FILLERS and (dur >= 0.45 or (tok and tok in {prev_tok,next_tok})):
            rows.append({"start":float(w["s"]),"end":float(w["e"]),"reason":"filler_voiced"})
    for a,b in zip(selected, selected[1:]):
        gap = float(b["s"]) - float(a["e"])
        if gap >= 0.65:
            start = float(a["e"]) + 0.08
            end = float(b["s"]) - 0.08
            if end - start >= 0.12:
                rows.append({"start":start,"end":end,"reason":"empty_gap"})

    merged = merge_intervals(rows, lo, hi, 0.30)
    removed = sum(r["end"]-r["start"] for r in merged)
    final_est = raw_duration - removed
    if final_est < 30:
        raise RuntimeError(f"Microedição reduziria demais o corte: {final_est:.2f}s")
    meta = {
        "raw_duration":round(raw_duration,3),
        "planned_removed_seconds":round(removed,3),
        "estimated_final_duration":round(final_est,3),
        "semantic_requested":len(semantic),
        "intervals":merged,
    }
    return lo, hi, merged, meta


def render_microcut(scan: Path, lo: float, hi: float, removals: list[dict], edited: Path) -> None:
    keep=[]; cursor=lo; edge=0.035
    for row in removals:
        a=max(cursor,float(row["start"])-edge); b=min(hi,float(row["end"])+edge)
        if a > cursor + 0.03: keep.append((cursor,a))
        cursor=max(cursor,b)
    if cursor < hi-0.03: keep.append((cursor,hi))
    if not keep: raise RuntimeError("Nenhum intervalo útil restou.")
    filters=[]; inputs=[]
    for i,(a,b) in enumerate(keep):
        filters.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
        filters.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
        inputs.append(f"[v{i}][a{i}]")
    filters.append("".join(inputs)+f"concat=n={len(keep)}:v=1:a=1[v][a]")
    cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(scan),"-filter_complex",";".join(filters),"-map","[v]","-map","[a]","-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-b:a","160k","-movflags","+faststart",str(edited)]
    subprocess.run(cmd,check=True,timeout=600)


def horizontalize(edited: Path, out: Path) -> None:
    vf="scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1"
    cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(edited),"-vf",vf,"-map","0:v:0","-map","0:a:0","-c:v","libx264","-preset","veryfast","-crf","20","-maxrate","3500k","-bufsize","7000k","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)]
    subprocess.run(cmd,check=True,timeout=900)
    if not out.exists() or out.stat().st_size < 200_000:
        raise RuntimeError("Arquivo final inválido.")


def media_meta(path: Path) -> dict:
    p=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height:format=duration","-of","json",str(path)],capture_output=True,text=True,check=True)
    data=json.loads(p.stdout or "{}")
    streams=data.get("streams") or []
    if not streams: raise RuntimeError("Saída sem vídeo.")
    width=int(streams[0].get("width") or 0); height=int(streams[0].get("height") or 0)
    dur=float((data.get("format") or {}).get("duration") or 0)
    ratio=(width/height) if height else 0
    if width != 1280 or height != 720 or abs(ratio-(16/9)) > 0.001:
        raise RuntimeError(f"Saída X fora de 16:9 horizontal: {width}x{height}")
    return {"width":width,"height":height,"aspect_ratio":"16:9","orientation":"horizontal","duration":round(dur,3)}


def main() -> int:
    req=json.loads(REQ.read_text(encoding="utf-8")); plan=json.loads(PLAN.read_text(encoding="utf-8"))
    if plan.get("kind") != "X_MICROCUT_PLAN_V1": raise RuntimeError("Plano incompatível.")
    if str(req.get("account")) != "lucasyahn": raise RuntimeError("Conta inesperada.")
    policy=req.get("output_policy") or {}
    if policy.get("orientation") != "horizontal" or policy.get("aspect_ratio") != "16:9" or policy.get("source_class") != "long_form":
        raise RuntimeError("Política X exige origem longa e saída horizontal 16:9.")
    caption=" ".join(str(plan.get("caption") or "").split()).strip()
    if not caption or len(caption)>240: raise RuntimeError("Caption ausente ou longa demais.")
    lo,hi,removals,meta=plan_intervals(req,plan)
    WORK.mkdir(parents=True,exist_ok=True)
    scan=WORK/"scan.mp4"; edited=WORK/"edited.mp4"
    source_url=str((req.get("source") or {}).get("source_url") or "")
    prep.SCAN_START=int(req.get("scan_start") or 0); prep.SCAN_SECONDS=int(req.get("scan_seconds") or 300)
    prep.download_scan(source_url,scan)
    prep.probe_video(scan)
    render_microcut(scan,lo,hi,removals,edited)
    horizontalize(edited,OUT)
    out_meta=media_meta(OUT)
    meta["final_duration"]=out_meta["duration"]
    meta["file_bytes"]=OUT.stat().st_size
    meta["output_video"]=out_meta
    result={"kind":"X_RENDER_RESULT_V1","account":"lucasyahn","caption":caption,"source":req.get("source"),"scan_start":req.get("scan_start"),"segment_start":round(lo,3),"segment_end":round(hi,3),"microedit":meta,"output":str(OUT)}
    Path("x-render-result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("X_RENDER_OK="+json.dumps(meta,ensure_ascii=False,separators=(",",":")))
    return 0

if __name__ == "__main__": raise SystemExit(main())
