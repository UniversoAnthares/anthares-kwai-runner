#!/usr/bin/env python3
from __future__ import annotations

import json, os, re, shutil, subprocess, sys, unicodedata, urllib.parse, urllib.request
from pathlib import Path

import x_cloud_prepare as prep

WORK = Path('x-real-fullflow-work')
OUT = Path('x-cloud-output.mp4')
MODEL = os.getenv('X_WHISPER_MODEL', 'base')
SCAN_START = int(os.getenv('X_SCAN_START', '600'))
SCAN_SECONDS = int(os.getenv('X_SCAN_SECONDS', '300'))
PIPED_BASES = [x.strip().rstrip('/') for x in os.getenv('X_PIPED_BASES', ','.join([
    'https://pipedapi.kavin.rocks','https://pipedapi.leptons.xyz','https://pipedapi.nosebs.ru',
    'https://pipedapi-libre.kavin.rocks','https://piped-api.privacy.com.de','https://pipedapi.adminforge.de',
    'https://api.piped.yt','https://pipedapi.drgns.space','https://pipedapi.ducks.party',
    'https://piped-api.codespace.cz','https://pipedapi.reallyaweso.me','https://api.piped.private.coffee',
    'https://pipedapi.darkness.services','https://pipedapi.orangenet.cc','https://pipedapi.coldforge.xyz',
])).split(',') if x.strip()]
FILLERS = {'ah','ahn','ha','ham','hum','hmm','eh','e','er','uh','uhm','né','tipo'}
CTA = {'inscreva','inscrever','canal','like','curta','compartilhe','compartilhar','youtube','chat','live','superchat','membro'}


def norm(t: str) -> str:
    s = unicodedata.normalize('NFKD', str(t or '')).encode('ascii','ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]+','',s.casefold())


def http_json(url: str, timeout=18):
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def quality_height(row: dict) -> int:
    for key in ('quality','qualityLabel','resolution'):
        m = re.search(r'(\d{3,4})p?', str(row.get(key) or ''))
        if m: return int(m.group(1))
    try: return int(row.get('height') or 0)
    except Exception: return 0


def piped_formats(base: str, vid: str):
    data = http_json(f'{base}/streams/{urllib.parse.quote(vid)}')
    videos = [x for x in data.get('videoStreams',[]) if isinstance(x,dict) and str(x.get('url') or '').startswith('http')]
    audios = [x for x in data.get('audioStreams',[]) if isinstance(x,dict) and str(x.get('url') or '').startswith('http')]
    if not videos: raise RuntimeError('no video streams')
    eligible = [x for x in videos if 0 < quality_height(x) <= 720] or videos
    def vscore(x):
        mime=(str(x.get('mimeType') or '')+' '+str(x.get('codec') or '')+' '+str(x.get('format') or '')).lower()
        return (1 if ('mp4' in mime or 'h264' in mime or 'avc' in mime) else 0, quality_height(x), int(x.get('bitrate') or 0))
    video=max(eligible,key=vscore)
    audio=None
    if audios:
        def ascore(x):
            mime=(str(x.get('mimeType') or '')+' '+str(x.get('codec') or '')+' '+str(x.get('format') or '')).lower()
            return (1 if ('mp4' in mime or 'm4a' in mime or 'aac' in mime) else 0, int(x.get('bitrate') or 0))
        audio=max(audios,key=ascore)
    return video,audio,data


def download_scan(source: dict, out: Path) -> str:
    vid=source['video_id']; errors=[]
    for base in PIPED_BASES:
        try:
            v,a,data=piped_formats(base,vid)
            vurl=str(v['url']); aurl=str(a['url']) if a else ''
            out.unlink(missing_ok=True)
            if aurl:
                cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-user_agent','Mozilla/5.0',
                     '-ss',str(SCAN_START),'-i',vurl,'-ss',str(SCAN_START),'-i',aurl,'-t',str(SCAN_SECONDS),
                     '-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','21','-c:a','aac','-b:a','160k','-movflags','+faststart',str(out)]
            else:
                cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-user_agent','Mozilla/5.0',
                     '-ss',str(SCAN_START),'-i',vurl,'-t',str(SCAN_SECONDS),'-map','0:v:0','-map','0:a:0?',
                     '-c:v','libx264','-preset','veryfast','-crf','21','-c:a','aac','-b:a','160k','-movflags','+faststart',str(out)]
            print(f'X_REAL_SOURCE_ATTEMPT=PIPED base={base} height={quality_height(v)} audio={bool(aurl)}',flush=True)
            subprocess.run(cmd,check=True,timeout=900)
            if out.exists() and out.stat().st_size>300_000:
                print(f'X_REAL_SOURCE_ROUTE=PIPED base={base}',flush=True)
                return base
        except Exception as exc:
            errors.append(f'{base}: {type(exc).__name__}: {str(exc)[:180]}')
            print('X_REAL_SOURCE_FAIL='+errors[-1],flush=True)
    print('X_REAL_PIPED_EXHAUSTED; falling back to existing downloader',flush=True)
    try:
        prep.SCAN_START=SCAN_START; prep.SCAN_SECONDS=SCAN_SECONDS
        prep.download_scan(source['source_url'],out)
        return 'existing-fallback'
    except Exception as exc:
        errors.append(f'existing: {type(exc).__name__}: {str(exc)[:220]}')
        raise RuntimeError('all real-source routes failed: '+' | '.join(errors[-8:]))


def probe(path: Path) -> dict:
    p=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height:format=duration','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=30)
    d=json.loads(p.stdout or '{}'); st=(d.get('streams') or [{}])[0]; fmt=d.get('format') or {}
    w=int(st.get('width') or 0); h=int(st.get('height') or 0); dur=float(fmt.get('duration') or 0)
    if not w or not h or w<=h or abs(w/h-16/9)>0.04: raise RuntimeError(f'X source is not horizontal 16:9: {w}x{h}')
    if dur < 140: raise RuntimeError(f'scan too short: {dur:.2f}s')
    return {'width':w,'height':h,'duration':dur,'aspect_ratio':round(w/h,4)}


def transcribe(path: Path):
    from faster_whisper import WhisperModel
    model=WhisperModel(MODEL,device='cpu',compute_type='int8')
    segments,_=model.transcribe(str(path),language='pt',beam_size=5,vad_filter=True,word_timestamps=True,condition_on_previous_text=True)
    words=[]
    for seg in segments:
        for w in getattr(seg,'words',None) or []:
            t=str(getattr(w,'word','') or '').strip(); s=float(getattr(w,'start',0) or 0); e=float(getattr(w,'end',s) or s)
            if t and e>s: words.append({'id':len(words),'s':s,'e':e,'t':t,'n':norm(t)})
    if len(words)<100: raise RuntimeError('transcript too small')
    return words


def choose_window(words, total):
    target=125.0; best=None
    for i in range(0,len(words),6):
        lo=words[i]['s']; hi=min(total,lo+target)
        if hi-lo<112: continue
        subset=[w for w in words if lo<=w['s'] and w['e']<=hi]
        if len(subset)<80: continue
        toks=[w['n'] for w in subset if w['n']]
        content=[t for t in toks if len(t)>=4 and t not in FILLERS]
        unique=len(set(content)); density=len(subset)/(hi-lo); cta=sum(t in CTA for t in toks); fillers=sum(t in FILLERS for t in toks)
        punctuation=sum(str(w['t']).endswith(('.', '?', '!')) for w in subset)
        score=unique*1.2+density*24+punctuation*1.5-cta*10-fillers*0.5
        if lo<15 or hi>total-8: score-=30
        if best is None or score>best[0]: best=(score,lo,hi,subset)
    if not best: raise RuntimeError('no strategic long-form window')
    score,lo,hi,subset=best
    # align boundaries to nearby punctuation without shrinking below 112s
    starts=[w for w in words if lo-6<=w['e']<=lo+6 and str(w['t']).endswith(('.', '?', '!'))]
    if starts:
        candidate=min(starts,key=lambda w:abs(w['e']-lo))['e']
        if hi-candidate>=112: lo=candidate
    ends=[w for w in words if hi-6<=w['e']<=hi+6 and str(w['t']).endswith(('.', '?', '!'))]
    if ends:
        candidate=min(ends,key=lambda w:abs(w['e']-hi))['e']
        if candidate-lo<=135 and candidate-lo>=112: hi=candidate
    selected=[w for w in words if lo<=w['s'] and w['e']<=hi]
    return lo,hi,selected,score


def removals(selected, lo, hi):
    rows=[]
    for i,w in enumerate(selected):
        t=w['n']; dur=w['e']-w['s']; prev=selected[i-1]['n'] if i else ''; nxt=selected[i+1]['n'] if i+1<len(selected) else ''
        if t in FILLERS and (dur>=0.42 or (t and t in {prev,nxt})):
            rows.append({'start':w['s'],'end':w['e'],'reason':'filler'})
        if i and t and t==prev and dur<1.2:
            rows.append({'start':selected[i-1]['s'],'end':selected[i-1]['e'],'reason':'immediate_repeat'})
    for a,b in zip(selected,selected[1:]):
        gap=b['s']-a['e']
        if gap>=0.85:
            s=a['e']+0.10; e=b['s']-0.10
            if e-s>=0.18: rows.append({'start':s,'end':e,'reason':'silence'})
    rows.sort(key=lambda r:(r['start'],r['end'])); merged=[]
    for r in rows:
        if not merged or r['start']>merged[-1]['end']+0.05: merged.append({'start':r['start'],'end':r['end'],'reasons':[r['reason']]})
        else:
            merged[-1]['end']=max(merged[-1]['end'],r['end']); merged[-1]['reasons'].append(r['reason'])
    accepted=[]; used=0; budget=min(12.0,max(0,(hi-lo)-105.0))
    for r in sorted(merged,key=lambda x:(x['end']-x['start'],x['start'])):
        span=r['end']-r['start']
        if used+span<=budget:
            accepted.append(r); used+=span
    return sorted(accepted,key=lambda r:r['start'])


def render(scan: Path,lo,hi,remove,out: Path):
    keep=[]; cur=lo; edge=.03
    for r in remove:
        a=max(cur,r['start']-edge); b=min(hi,r['end']+edge)
        if a>cur+.03: keep.append((cur,a))
        cur=max(cur,b)
    if cur<hi-.03: keep.append((cur,hi))
    flt=[]; seq=[]
    for i,(a,b) in enumerate(keep):
        flt.append(f'[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]')
        flt.append(f'[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]')
        seq.append(f'[v{i}][a{i}]')
    flt.append(''.join(seq)+f'concat=n={len(keep)}:v=1:a=1[v][a]')
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(scan),'-filter_complex',';'.join(flt),'-map','[v]','-map','[a]',
                    '-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1',
                    '-c:v','libx264','-preset','veryfast','-crf','20','-maxrate','3500k','-bufsize','7000k','-c:a','aac','-b:a','160k','-movflags','+faststart',str(out)],check=True,timeout=900)


def caption_for(source: dict, selected):
    title=str(source.get('title') or '').strip()
    if 'homem do elevador' in title.casefold():
        return 'Uma conversa aparentemente casual dentro de um elevador pode carregar muito mais do que parece. O que muda quando o silêncio começa a revelar a história? #Literatura #Contos'
    text=' '.join(w['t'] for w in selected[:34]).strip()
    text=re.sub(r'\s+([,.;!?])',r'\1',text)
    return (text[:205].rsplit(' ',1)[0]+'… #Literatura')[:240]


def main():
    WORK.mkdir(exist_ok=True)
    source=prep.discover_source()
    print('X_REAL_SOURCE_DISCOVERED='+json.dumps(source,ensure_ascii=False),flush=True)
    scan=WORK/'scan.mp4'; route=download_scan(source,scan); meta=probe(scan)
    print('X_REAL_SOURCE_META='+json.dumps(meta),flush=True)
    words=transcribe(scan)
    lo,hi,selected,score=choose_window(words,meta['duration'])
    remove=removals(selected,lo,hi)
    removed=sum(r['end']-r['start'] for r in remove)
    render(scan,lo,hi,remove,OUT)
    outmeta=probe(OUT)
    if outmeta['duration']<105 or outmeta['duration']>135: raise RuntimeError(f'final long-form duration invalid: {outmeta["duration"]}')
    caption=caption_for(source,selected)
    result={
        'kind':'X_REAL_FULLFLOW_RESULT_V1','account':'lucasyahn','caption':caption,'source':source,'source_route':route,
        'scan_start':SCAN_START,'strategic_score':round(score,3),'segment_start':round(lo,3),'segment_end':round(hi,3),
        'microedit':{'removed_seconds':round(removed,3),'intervals':remove,'final_duration':round(outmeta['duration'],3)},
        'output_video':{'width':outmeta['width'],'height':outmeta['height'],'aspect_ratio':'16:9','orientation':'horizontal','duration':round(outmeta['duration'],3)},
        'selected_transcript':' '.join(w['t'] for w in selected)
    }
    Path('x-render-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('X_REAL_FULLFLOW_OK='+json.dumps({k:result[k] for k in ('source_route','segment_start','segment_end','microedit','output_video','caption')},ensure_ascii=False,separators=(',',':')),flush=True)
    return 0

if __name__=='__main__': raise SystemExit(main())
