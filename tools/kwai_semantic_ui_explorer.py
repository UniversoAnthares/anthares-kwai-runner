#!/usr/bin/env python3
import os,re,subprocess,time,xml.etree.ElementTree as ET

CASE=int(os.environ.get('CASE_ID','1'))
MAX_STEPS=12 + (CASE % 5)

PRIMARY=[
 'profile','perfil','me','eu','account','conta','login','log in','sign in','entrar',
 'email','e-mail','phone','telefone','mobile','celular','continue','continuar','next','avançar',
 'accept','aceitar','agree','concordo','allow','permitir','skip','pular'
]
SECONDARY=['mine','my','user','usuario','usuário','settings','configurações','more','mais','home','início']

def adb(*args,timeout=20):
    p=subprocess.run(['adb',*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout)
    return p.stdout

def dump():
    adb('shell','uiautomator','dump','/sdcard/kwai-explore.xml')
    xml=adb('exec-out','cat','/sdcard/kwai-explore.xml')
    if '<hierarchy' not in xml:
        return []
    try:return list(ET.fromstring(xml).iter('node'))
    except Exception:return []

def text(n):
    return ((n.get('text') or '')+' '+(n.get('content-desc') or '')+' '+(n.get('resource-id') or '')).strip().lower()

def bounds(n):
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds') or '')
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups());return ((x1+x2)//2,(y1+y2)//2)

def editable(ns):
    return [n for n in ns if (n.get('class') or '').endswith('EditText') or n.get('editable')=='true']

def login_ready(ns):
    s=' '.join(text(n) for n in ns)
    ed=editable(ns)
    markers=('password','senha','email','e-mail','phone','telefone','mobile','celular','log in','login','sign in','entrar')
    return bool(ed) or any(k in s for k in markers)

def clickables(ns):
    out=[]
    for n in ns:
        if n.get('clickable')=='true' or n.get('focusable')=='true':
            p=bounds(n)
            if p:out.append(n)
    return out

def score(n,step):
    t=text(n)
    score=0
    for i,k in enumerate(PRIMARY):
        if k in t: score += 300 - i*3
    for i,k in enumerate(SECONDARY):
        if k in t: score += 80 - i*2
    # Deterministic per-case diversity without random nondeterminism.
    p=bounds(n) or (0,0)
    score += ((p[0]*31 + p[1]*17 + CASE*97 + step*53) % 71)
    # Prefer bottom navigation in some cases when labels are weak.
    if CASE % 3 == 0 and p[1] > 1500: score += 70
    if CASE % 7 == 0 and p[0] > 700: score += 40
    return score

def tap_node(n):
    p=bounds(n)
    if not p:return False
    adb('shell','input','tap',str(p[0]),str(p[1]))
    time.sleep(1.2 + (CASE % 4)*0.25)
    return True

def open_app():
    adb('shell','am','force-stop','com.kwai.video')
    adb('shell','monkey','-p','com.kwai.video','-c','android.intent.category.LAUNCHER','1')
    time.sleep(4 + (CASE % 5))

open_app()
seen=set()
for step in range(MAX_STEPS):
    ns=dump()
    if not ns:
        print(f'KWAI_EXPLORE_STEP={step} EMPTY_UI=1')
        adb('shell','input','keyevent','KEYCODE_BACK');time.sleep(1);continue
    if login_ready(ns):
        print(f'KWAI_EXPLORE_LOGIN_SURFACE=1 STEP={step} EDITS={len(editable(ns))}')
        raise SystemExit(0)
    cand=clickables(ns)
    ranked=sorted(cand,key=lambda n:score(n,step),reverse=True)
    chosen=None
    for n in ranked:
        key=(text(n),n.get('bounds'))
        if key not in seen:
            chosen=n;seen.add(key);break
    if chosen is None:
        # Geometric fallback: 5 bottom-nav probes rotated by case.
        xs=[108,324,540,756,972]
        x=xs[(CASE+step)%len(xs)]
        y=1770 - (CASE%3)*35
        print(f'KWAI_EXPLORE_FALLBACK_TAP={x},{y} STEP={step}')
        adb('shell','input','tap',str(x),str(y));time.sleep(1.5)
        continue
    print(f'KWAI_EXPLORE_STEP={step} SCORE={score(chosen,step)} TARGET={text(chosen)[:120]!r} BOUNDS={chosen.get("bounds")}')
    tap_node(chosen)

ns=dump()
if login_ready(ns):
    print(f'KWAI_EXPLORE_LOGIN_SURFACE=1 STEP=FINAL EDITS={len(editable(ns))}')
    raise SystemExit(0)
print(f'KWAI_EXPLORE_LOGIN_SURFACE=0 STEPS={MAX_STEPS} NODES={len(ns)} EDITS={len(editable(ns))}')
raise SystemExit(4)
