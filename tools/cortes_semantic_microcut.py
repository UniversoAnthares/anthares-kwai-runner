#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math, re, subprocess, unicodedata
from collections import Counter
from pathlib import Path

FILLERS={"ah","ahn","ahh","ahem","hum","hmm","uh","uhm","eh","ehh","ehhh","er","tipo","ne"}
STOP={"a","o","as","os","um","uma","uns","umas","de","da","do","das","dos","e","ou","que","em","no","na","nos","nas","para","por","com","sem","se","eu","voce","voces","ele","ela","eles","elas","meu","minha","seu","sua","isso","isto","esse","essa","aquele","aquela","como","mais","menos","muito","muita","muitos","muitas","ja","nao","sim","ser","estar","ter","foi","vai","vou","tem","tinha","aqui","ali","entao","porque","quando","onde","quem","qual","quais"}
INTRO_PATTERNS=[
    r"\bbom dia\b",r"\bboa tarde\b",r"\bboa noite\b",r"\bbem vind",r"\bsejam bem vind",
    r"\bvamos esperar\b",r"\bquem esta chegando\b",r"\bquem chegou\b",r"\bcomecar a live\b",
    r"\bnessa live\b",r"\bna live de hoje\b",r"\bdeixa o like\b",r"\bdeixe o like\b",
    r"\bse inscrev",r"\binscrev",r"\bcompartilh",r"\bativa o sininho\b",r"\bcanal\b",
    r"\bsuperchat\b",r"\bmembro do canal\b",r"\bmanda no chat\b",r"\bchat\b"
]


def norm(s:str)->str:
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+","",s)


def plain(s:str)->str:
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode("ascii").casefold()
    return re.sub(r"\s+"," ",s).strip()


def parse_json3(path:Path):
    data=json.loads(path.read_text(encoding="utf-8"))
    words=[]; events=[]
    for ev in data.get("events",[]):
        if not isinstance(ev,dict) or not ev.get("segs"): continue
        base=float(ev.get("tStartMs",0))/1000.0
        dur=max(0.05,float(ev.get("dDurationMs",0))/1000.0)
        segs=[x for x in ev.get("segs",[]) if isinstance(x,dict) and str(x.get("utf8","")).strip()]
        if not segs: continue
        text="".join(str(x.get("utf8","")).replace("\n"," ") for x in segs).strip()
        if text: events.append({"s":base,"e":base+dur,"text":text})
        offsets=[float(x.get("tOffsetMs",0))/1000.0 for x in segs]
        for i,x in enumerate(segs):
            raw=str(x.get("utf8","")).replace("\n"," ").strip()
            toks=re.findall(r"[\wÀ-ÿ'-]+|[.!?]",raw,flags=re.UNICODE)
            if not toks: continue
            ss=base+offsets[i]
            ee=base+(offsets[i+1] if i+1<len(offsets) else dur)
            ee=max(ss+0.08,ee)
            span=max(0.08,(ee-ss)/max(1,len(toks)))
            for j,t in enumerate(toks):
                a=ss+j*span; b=min(ee,a+span)
                words.append({"s":a,"e":max(a+0.04,b),"t":t,"n":norm(t)})
    if len(words)<100: raise SystemExit("TRANSCRIPT_TOO_SMALL")
    return words,events


def candidate_windows(words,events,min_start,target,min_len,max_len):
    total=max(w["e"] for w in words)
    starts=[]
    for ev in events:
        s=float(ev["s"])
        if s>=min_start and s<=total-min_len: starts.append(s)
    starts=sorted(set(round(x,2) for x in starts))
    # Keep natural event boundaries but cap density to roughly one candidate / 8 s.
    filtered=[]; last=-999
    for s in starts:
        if s-last>=7.5: filtered.append(s); last=s
    rows=[]
    for s in filtered:
        desired=s+target
        ends=[float(ev["e"]) for ev in events if s+min_len<=float(ev["e"])<=s+max_len]
        if not ends: continue
        e=min(ends,key=lambda x:abs(x-desired))
        subset=[w for w in words if w["s"]>=s and w["e"]<=e and w["n"]]
        if len(subset)<90: continue
        text=" ".join(w["t"] for w in subset)
        rows.append({"s":s,"e":e,"words":subset,"text":text})
    return rows,total


def score_windows(rows):
    if not rows: raise SystemExit("NO_SEMANTIC_CANDIDATES")
    docs=[]
    for r in rows:
        toks=[w["n"] for w in r["words"] if len(w["n"])>=4 and w["n"] not in STOP and w["n"] not in FILLERS]
        docs.append(set(toks))
    df=Counter(t for d in docs for t in d); n=max(1,len(rows))
    for r in rows:
        toks=[w["n"] for w in r["words"] if w["n"]]
        content=[t for t in toks if len(t)>=4 and t not in STOP and t not in FILLERS]
        counts=Counter(content)
        tfidf=sum((1+math.log(c))*math.log((n+1)/(1+df[t])+1.0) for t,c in counts.items())
        unique=len(counts); diversity=unique/max(1,len(content)); density=len(content)/max(1.0,r["e"]-r["s"])
        half=(r["s"]+r["e"])/2
        left=set(w["n"] for w in r["words"] if w["s"]<half and len(w["n"])>=5 and w["n"] not in STOP)
        right=set(w["n"] for w in r["words"] if w["s"]>=half and len(w["n"])>=5 and w["n"] not in STOP)
        coherence=len(left & right)
        p=plain(r["text"])
        intro=sum(1 for pat in INTRO_PATTERNS if re.search(pat,p))
        fillers=sum(1 for t in toks if t in FILLERS)
        immediate=sum(1 for a,b in zip(toks,toks[1:]) if a and a==b)
        lexical=sum(1 for t in content if len(t)>=7)
        # Prefer sustained, specific discussion; heavily reject intro/CTA/admin chatter.
        r["score"]=tfidf*1.5+unique*0.45+diversity*45+density*18+coherence*3.0+lexical*0.08-intro*38-fillers*0.9-immediate*2.5
        r["metrics"]={"unique_content":unique,"diversity":round(diversity,3),"content_density":round(density,3),"coherence_terms":coherence,"intro_hits":intro,"fillers":fillers,"immediate_repeats":immediate}
    rows.sort(key=lambda x:x["score"],reverse=True)
    return rows


def select(args):
    words,events=parse_json3(Path(args.transcript))
    rows,total=candidate_windows(words,events,args.min_start,args.target,args.min_len,args.max_len)
    ranked=score_windows(rows)
    # Never accept an intro/CTA-heavy candidate when a clean candidate exists.
    clean=[r for r in ranked if r["metrics"]["intro_hits"]==0]
    if not clean: raise SystemExit("NO_NONINTRO_SEMANTIC_CANDIDATE")
    best=clean[0]
    if best["metrics"]["unique_content"] < 22 or best["metrics"]["content_density"] < 0.35:
        raise SystemExit("SEMANTIC_CONTENT_TOO_WEAK")
    plan={
        "kind":"ANTHARES_CORTES_SEMANTIC_PLAN_V1","transcript_words":len(words),"source_duration":round(total,3),
        "source_start":round(best["s"],3),"source_end":round(best["e"],3),"source_duration_selected":round(best["e"]-best["s"],3),
        "semantic_score":round(best["score"],3),"metrics":best["metrics"],"selected_transcript":best["text"],
        "alternatives":[{"start":round(r["s"],3),"end":round(r["e"],3),"score":round(r["score"],3),"metrics":r["metrics"],"text":r["text"][:500]} for r in ranked[:5]]
    }
    Path(args.output).write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    print("SEMANTIC_SELECTION=PROVEN")
    print(f"SEMANTIC_INTERVAL={plan['source_start']}-{plan['source_end']}")
    print(f"SEMANTIC_SCORE={plan['semantic_score']}")
    print("SEMANTIC_PREVIEW="+best["text"][:700].replace("\n"," "))


def whisper_words(path:Path,model_name:str):
    from faster_whisper import WhisperModel
    model=WhisperModel(model_name,device="cpu",compute_type="int8")
    segs,_=model.transcribe(str(path),language="pt",beam_size=5,vad_filter=True,word_timestamps=True,condition_on_previous_text=True)
    out=[]
    for seg in segs:
        for w in getattr(seg,"words",None) or []:
            t=str(getattr(w,"word","") or "").strip(); s=float(getattr(w,"start",0) or 0); e=float(getattr(w,"end",s) or s)
            if t and e>s: out.append({"s":s,"e":e,"t":t,"n":norm(t)})
    if len(out)<30: raise SystemExit("WHISPER_TRANSCRIPT_TOO_SMALL")
    return out


def build_removals(words,total):
    rows=[]
    for i,w in enumerate(words):
        t=w["n"]; dur=w["e"]-w["s"]; prev=words[i-1]["n"] if i else ""; nxt=words[i+1]["n"] if i+1<len(words) else ""
        left_gap=w["s"]-words[i-1]["e"] if i else 9; right_gap=words[i+1]["s"]-w["e"] if i+1<len(words) else 9
        if t in FILLERS and (dur>=0.38 or t==prev or t==nxt or (left_gap>=0.18 and right_gap>=0.18)):
            rows.append({"start":w["s"],"end":w["e"],"reason":"filler"})
        if i and t and t==prev and dur<1.4:
            rows.append({"start":words[i-1]["s"],"end":words[i-1]["e"],"reason":"repeated_word"})
    toks=[w["n"] for w in words]
    occupied=set()
    for size in range(7,1,-1):
        i=0
        while i+2*size<=len(words):
            a=toks[i:i+size]; b=toks[i+size:i+2*size]
            if all(a) and a==b and not any(j in occupied for j in range(i,i+size)):
                rows.append({"start":words[i]["s"],"end":words[i+size-1]["e"],"reason":"repeated_phrase"}); occupied.update(range(i,i+size)); i+=2*size
            else:i+=1
    for a,b in zip(words,words[1:]):
        gap=b["s"]-a["e"]
        if gap>=0.58:
            s=a["e"]+0.10; e=b["s"]-0.10
            if e-s>=0.20: rows.append({"start":s,"end":e,"reason":"pause"})
    rows.sort(key=lambda r:(r["start"],r["end"])); merged=[]
    for r in rows:
        a=max(0.0,r["start"]); b=min(total,r["end"])
        if b-a<0.10: continue
        if not merged or a>merged[-1]["end"]+0.06: merged.append({"start":a,"end":b,"reasons":[r["reason"]]})
        else: merged[-1]["end"]=max(merged[-1]["end"],b); merged[-1]["reasons"].append(r["reason"])
    budget=min(total*0.24,max(0,total-50.0)); accepted=[]; used=0.0
    # Prefer fillers/repetitions before pauses, then shorter edits.
    def priority(r):
        semantic=0 if any(x in r["reasons"] for x in ("filler","repeated_word","repeated_phrase")) else 1
        return (semantic,r["end"]-r["start"],r["start"])
    for r in sorted(merged,key=priority):
        span=r["end"]-r["start"]
        if used+span<=budget: accepted.append(r); used+=span
    return sorted(accepted,key=lambda r:r["start"])


def duration(path:Path):
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())


def render_without(src:Path,rows,out:Path,total:float):
    keep=[]; cur=0.0; edge=.025
    for r in rows:
        a=max(cur,r["start"]-edge); b=min(total,r["end"]+edge)
        if a>cur+.025: keep.append((cur,a))
        cur=max(cur,b)
    if cur<total-.025: keep.append((cur,total))
    if len(keep)<2: raise SystemExit("MICROCUT_KEEP_PARTS_LT_2")
    flt=[]; seq=[]
    for i,(a,b) in enumerate(keep):
        flt.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
        flt.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
        seq.append(f"[v{i}][a{i}]")
    flt.append("".join(seq)+f"concat=n={len(keep)}:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(src),"-filter_complex",";".join(flt),"-map","[v]","-map","[a]","-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)],check=True,timeout=1200)
    return keep


def microcut(args):
    src=Path(args.input); out=Path(args.output); total=duration(src); words=whisper_words(src,args.model)
    rows=build_removals(words,total)
    if not rows: raise SystemExit("MICROCUT_REQUIRED_BUT_NONE_FOUND")
    keep=render_without(src,rows,out,total); final=duration(out); removed=max(0,total-final)
    if removed<0.20 or len(keep)<2: raise SystemExit("MICROCUT_NOT_MATERIAL")
    reasons=Counter(x for r in rows for x in r["reasons"])
    report={"kind":"ANTHARES_CORTES_MICROCUT_V1","original_duration":round(total,3),"final_duration":round(final,3),"removed_seconds":round(removed,3),"intervals":len(rows),"keep_parts":len(keep),"reasons":dict(reasons),"removals":rows,"transcript":" ".join(w["t"] for w in words)}
    Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("MICROCUTS=PROVEN")
    print(f"MICROCUT_REMOVED_SECONDS={report['removed_seconds']}")
    print(f"MICROCUT_INTERVALS={report['intervals']}")
    print("MICROCUT_REASONS="+json.dumps(report["reasons"],ensure_ascii=False,separators=(",",":")))


def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("select"); s.add_argument("--transcript",required=True); s.add_argument("--output",required=True); s.add_argument("--min-start",type=float,default=240); s.add_argument("--target",type=float,default=90); s.add_argument("--min-len",type=float,default=70); s.add_argument("--max-len",type=float,default=110)
    m=sub.add_parser("microcut"); m.add_argument("--input",required=True); m.add_argument("--output",required=True); m.add_argument("--report",required=True); m.add_argument("--model",default="small")
    a=p.parse_args(); select(a) if a.cmd=="select" else microcut(a)

if __name__=="__main__": main()
