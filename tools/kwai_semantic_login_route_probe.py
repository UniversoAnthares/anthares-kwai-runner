#!/usr/bin/env python3
import os,re,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from kwai_login_ui_locator import login_surface_kind

PKG='com.kwai.video'
ROUTE=os.getenv('KWAI_ROUTE','me_direct')
NETWORK=os.getenv('KWAI_NETWORK','baseline')
SETTLE=float(os.getenv('KWAI_SETTLE','3'))
REPORT=Path('semantic-login-route.txt')
REPORT.write_text('',encoding='utf-8')


def log(s):
    print(s,flush=True)
    with REPORT.open('a',encoding='utf-8') as f:f.write(s+'\n')

def adb(*args,timeout=25):
    return subprocess.run(['adb',*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)

def dump(tag):
    for compressed in (False,True,False):
        cmd=['shell','uiautomator','dump']
        if compressed:cmd.append('--compressed')
        cmd.append('/sdcard/kwai-semantic.xml')
        try:
            adb(*cmd,timeout=18)
            p=adb('exec-out','cat','/sdcard/kwai-semantic.xml',timeout=18)
            if '<hierarchy' in p.stdout:
                Path(f'semantic-{tag}.xml').write_text(p.stdout,encoding='utf-8')
                return p.stdout
        except Exception:pass
        time.sleep(1)
    return ''

def root_nodes(xml):
    try:
        root=ET.fromstring(xml);return root,list(root.iter('node'))
    except Exception:return None,[]

def rid(n):return (n.get('resource-id') or '').split('/')[-1]
def label(n):return ((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip().casefold()
def box(n):
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds') or '')
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups())
    return (x1,y1,x2,y2) if x2>x1 and y2>y1 else None
def center(n):
    b=box(n)
    return ((b[0]+b[2])//2,(b[1]+b[3])//2) if b else None

def tap_xy(p,name):
    if not p:return False
    adb('shell','input','tap',str(p[0]),str(p[1]));log('ACTION='+name);time.sleep(max(1,SETTLE));return True

def clickable_center(root,node):
    p=center(node)
    if root is None:return p
    parents={c:par for par in root.iter() for c in par}
    cur=node
    for _ in range(5):
        if cur is None:break
        if cur.get('clickable')=='true' and center(cur):return center(cur)
        cur=parents.get(cur)
    return p

def find_id(ns,*ids):
    for wanted in ids:
        for n in ns:
            if rid(n)==wanted and center(n):return n
    return None

def find_label(ns,*words):
    wanted={x.casefold() for x in words}
    for n in ns:
        if label(n) in wanted and center(n):return n
    return None

def success(xml,ns):
    # Must match the selector that immediately follows this probe. The old
    # resource-ID-only check accepted a Google button as an email chooser.
    surface=login_surface_kind(ns,xml)
    if surface=='chooser':
        log('KWAI_NATIVE_LOGIN_CHOOSER_VISIBLE=1');return True
    if surface=='form':
        log('KWAI_NATIVE_LOGIN_FORM_VISIBLE=1');return True
    return False

def clear_known_gate(root,ns):
    for key in ('bt_interest_skip_top_right','signin_fre_continue_button'):
        n=find_id(ns,key)
        if n is not None:return tap_xy(clickable_center(root,n),key)
    if any('interest' in rid(x) for x in ns):
        n=find_label(ns,'skip','pular','not now','agora não')
        if n is not None:return tap_xy(clickable_center(root,n),'skip_interest_label')
    n=find_id(ns,'permission_deny_button','permission_allow_button')
    if n is not None:return tap_xy(clickable_center(root,n),'permission_gate')
    n=find_label(ns,'not now','maybe later','agora não','mais tarde')
    if n is not None:return tap_xy(clickable_center(root,n),'dismiss_optional_gate')
    return False

def profile_target(root,ns):
    n=find_id(ns,'id_home_bottom_tab_me')
    if n is not None:return clickable_center(root,n)
    for n in ns:
        if label(n) in {'me','profile','perfil','eu'} and center(n):return clickable_center(root,n)
    return None

def profile_content(root,ns):
    n=find_id(ns,'indie_profile_content')
    return clickable_center(root,n) if n is not None else None

def login_target(root,ns):
    for key in ('login_container','login_button','btn_login','tv_login','login_platform_expand_text'):
        n=find_id(ns,key)
        if n is not None:return clickable_center(root,n)
    n=find_label(ns,'log in','login','sign in','entrar','fazer login','log in / sign up','log in or sign up')
    return clickable_center(root,n) if n is not None else None

def relaunch():
    adb('shell','am','force-stop',PKG);time.sleep(1)
    adb('shell','monkey','-p',PKG,'-c','android.intent.category.LAUNCHER','1');time.sleep(max(3,SETTLE))

def ensure_network(reason='initial'):
    log('NETWORK_REPAIR='+reason+' MODE='+NETWORK)
    adb('shell','cmd','connectivity','airplane-mode','disable')
    adb('shell','settings','put','global','airplane_mode_on','0')
    adb('shell','svc','data','enable')
    adb('shell','svc','wifi','enable')
    if NETWORK=='wifi_cycle':
        adb('shell','svc','wifi','disable');time.sleep(2);adb('shell','svc','wifi','enable');time.sleep(3)
    loops=8 if NETWORK in {'network_wait','wifi_cycle'} else 3
    ready=False
    for _ in range(loops):
        ip=adb('shell','ping','-c','1','-W','1','8.8.8.8',timeout=5)
        dns=adb('shell','ping','-c','1','-W','1','www.google.com',timeout=5)
        if ip.returncode==0 and dns.returncode==0:
            ready=True;break
        time.sleep(1)
    log('ANDROID_NETWORK_READY='+str(int(ready)))
    log('AIRPLANE_MODE='+adb('shell','settings','get','global','airplane_mode_on').stdout.strip())

def state(tag):
    xml=dump(tag);root,ns=root_nodes(xml)
    if not xml:return xml,root,ns
    ids={rid(n) for n in ns}
    unconnected=any('un_connected_network' in x for x in ids)
    log(f'STATE={tag} NODES={len(ns)} PID='+(adb('shell','pidof',PKG).stdout.strip() or 'none'))
    log('HAS_ME='+str(int('id_home_bottom_tab_me' in ids))+' HAS_LOGIN_CONTAINER='+str(int('login_container' in ids))+' HAS_UNCONNECTED='+str(int(unconnected)))
    if unconnected:ensure_network('ui-unconnected')
    return xml,root,ns

def open_profile_then_login(tag):
    xml,root,ns=state(tag+'-before-me')
    if success(xml,ns):return True
    if clear_known_gate(root,ns):
        xml,root,ns=state(tag+'-after-gate')
    p=profile_target(root,ns)
    if p:tap_xy(p,tag+'-me')
    for i in range(5):
        xml,root,ns=state(f'{tag}-profile-{i}')
        if success(xml,ns):return True
        if clear_known_gate(root,ns):continue
        q=login_target(root,ns)
        if q:
            tap_xy(q,tag+'-login')
            xml,root,ns=state(f'{tag}-login-result-{i}')
            if success(xml,ns):return True
        time.sleep(max(1,SETTLE/2))
    return False

ensure_network('initial')
relaunch()

for i in range(8):
    xml,root,ns=state(f'pre-{i}')
    if not xml:continue
    if success(xml,ns):log('SEMANTIC_LOGIN_ROUTE=PASS_PREEXISTING');sys.exit(0)
    if not clear_known_gate(root,ns):break

passed=False
if ROUTE=='me_direct':
    passed=open_profile_then_login('direct')
elif ROUTE=='me_retry':
    passed=open_profile_then_login('retry-a')
    if not passed:
        ensure_network('retry-route');passed=open_profile_then_login('retry-b')
elif ROUTE=='me_login_label':
    passed=open_profile_then_login('explicit')
elif ROUTE=='profile_content':
    xml,root,ns=state('content-home')
    p=profile_target(root,ns)
    if p:tap_xy(p,'content-me')
    xml,root,ns=state('content-profile')
    if success(xml,ns):passed=True
    else:
        q=profile_content(root,ns)
        if q:tap_xy(q,'profile-content')
        passed=open_profile_then_login('content-after')
elif ROUTE=='me_relaunch':
    xml,root,ns=state('relaunch-home')
    p=profile_target(root,ns)
    if p:tap_xy(p,'relaunch-me-before')
    relaunch();ensure_network('after-relaunch')
    passed=open_profile_then_login('relaunch-after')
else:
    log('UNKNOWN_ROUTE='+ROUTE);sys.exit(2)

if passed:
    log('SEMANTIC_LOGIN_ROUTE=PASS')
    sys.exit(0)

for i in range(12):
    xml,root,ns=state(f'late-{i}')
    if not xml:time.sleep(1);continue
    if success(xml,ns):log('SEMANTIC_LOGIN_ROUTE=PASS_LATE');sys.exit(0)
    if clear_known_gate(root,ns):continue
    if i in {2,5,8}:
        q=login_target(root,ns) or profile_target(root,ns)
        if q:tap_xy(q,'late-semantic-target')
    time.sleep(max(1,SETTLE/2))

Path('semantic-activities.txt').write_text(adb('shell','dumpsys','activity','activities').stdout,encoding='utf-8')
Path('semantic-connectivity.txt').write_text(adb('shell','dumpsys','connectivity').stdout[-40000:],encoding='utf-8')
Path('semantic-logcat.txt').write_text(adb('logcat','-d','-v','brief').stdout[-80000:],encoding='utf-8')
log('SEMANTIC_LOGIN_ROUTE=FAIL')
sys.exit(31)
