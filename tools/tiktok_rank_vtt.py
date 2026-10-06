#!/usr/bin/env python3
from pathlib import Path
import html, re, sys

root=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/canary-subs')
files=sorted(root.glob('*.vtt'), key=lambda p:(0 if '.pt' in p.name.lower() else 1,len(p.name)))
if not files: raise SystemExit('NO_VTT_SUBTITLE')
path=files[0]
print('TRANSCRIPT_FILE='+path.name)

def sec(ts):
    parts=ts.replace(',','.').split(':')
    if len(parts)==3: h,m,s=parts
    else: h='0'; m,s=parts
    return int(h)*3600+int(m)*60+float(s)

raw=path.read_text(encoding='utf-8',errors='replace').splitlines(); cues=[]; i=0
while i<len(raw):
    line=raw[i].strip()
    if '-->' not in line: i+=1; continue
    a,b=line.split('-->',1); a=a.strip().split()[0]; b=b.strip().split()[0]; i+=1; text=[]
    while i<len(raw) and raw[i].strip():
        t=re.sub(r'<[^>]+>','',raw[i]).strip()
        if t and not t.startswith('NOTE'): text.append(t)
        i+=1
    txt=re.sub(r'\s+',' ',html.unescape(' '.join(text))).strip()
    if txt: cues.append({'start':sec(a),'end':sec(b),'text':txt})
    i+=1
if not cues: raise SystemExit('EMPTY_TRANSCRIPT')

positive={'conto':4,'história':3,'historia':3,'personagem':4,'narrador':4,'narrativa':4,'texto':3,'leitor':3,'cena':3,'conflito':4,'estrutura':4,'escrita':3,'autor':3,'autora':3,'literatura':4,'tema':3,'diálogo':4,'dialogo':4,'ponto de vista':5,'foco narrativo':5,'protagonista':4,'descrição':3,'descricao':3,'tensão':4,'tensao':4,'ritmo':4,'final':3,'verossimilhança':5,'verossimilhanca':5,'arquétipo':5,'arquetipo':5,'porque':1,'portanto':2,'então':1,'entao':1,'significa':2,'funciona':2,'efeito':2,'problema':2,'solução':2,'solucao':2,'escolha':2}
negative={'boa noite':10,'bom dia':10,'boa tarde':10,'sejam bem':10,'inscreva':10,'like':10,'telegram':10,'pix':10,'superchat':10,'chat':4,'comentário':4,'comentario':4,'áudio':6,'audio':6,'microfone':6,'live':5,'ao vivo':5,'canal':4,'membro':4,'obrigado':5,'obrigada':5,'espera aí':6,'espera ai':6}
windows=[]
for idx,c in enumerate(cues):
    if c['start']<300: continue
    selected=[]; last=c['start']
    for d in cues[idx:]:
        if d['start']-last>4: break
        selected.append(d); last=max(last,d['end'])
        if last-c['start']>=60: break
        if last-c['start']>88: break
    dur=last-c['start']
    if dur<40 or dur>90: continue
    out=[]
    for d in selected:
        t=d['text']
        if out and (t==out[-1] or t in out[-1]): continue
        out.append(t)
    text=' '.join(out); low=text.casefold(); words=re.findall(r'\w+',low)
    if len(words)<60: continue
    score=sum(low.count(k)*v for k,v in positive.items())-sum(low.count(k)*v for k,v in negative.items())
    score+=min(8,low.count(' porque ')+2*low.count(' portanto ')+low.count(' então '))
    score-=max(0,text.count('?')-2)*2
    windows.append({'score':score,'start':c['start'],'end':last,'duration':dur,'text':text})
windows.sort(key=lambda x:(-x['score'],x['start']))
picked=[]
for w in windows:
    if any(max(w['start'],p['start'])<min(w['end'],p['end']) for p in picked): continue
    picked.append(w)
    if len(picked)>=10: break
if not picked: raise SystemExit('NO_CANDIDATE_WINDOWS')
def hms(x): x=int(x); return f'{x//3600:02d}:{(x%3600)//60:02d}:{x%60:02d}'
print('=== TOP CONTINUOUS CANDIDATES ===')
for n,w in enumerate(picked,1):
    print(f'\n--- CANDIDATE {n} score={w["score"]} start={hms(w["start"])} end={hms(w["end"])} duration={w["duration"]:.1f}s ---')
    print(w['text'][:6000])
print(f'\nTRANSCRIPT_CANDIDATES_READY={len(picked)}')
