#!/usr/bin/env python3
import os,re,subprocess,sys,time,xml.etree.ElementTree as ET

MODE=os.environ.get('KWAI_LOGIN_MODE','plain')
SETTLE=float(os.environ.get('KWAI_LOGIN_SETTLE','3'))
REPORT='kwai-home-login-state.txt'
open(REPORT,'w').close()

def log(s):
    print(s,flush=True)
    with open(REPORT,'a',encoding='utf-8') as f:f.write(s+'\n')

def run(*args,check=False,timeout=25):
    return subprocess.run(list(args),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout,check=check)

def adb(*args,check=False,timeout=25):
    return run('adb',*args,check=check,timeout=timeout)

def relaunch():
    adb('shell','am','force-stop','com.kwai.video')
    time.sleep(1)
    adb('shell','monkey','-p','com.kwai.video','-c','android.intent.category.LAUNCHER','1')
    time.sleep(max(3,SETTLE))

def dump_xml(tag='state'):
    for compressed in (False,True,False):
        cmd=['shell','uiautomator','dump']
        if compressed: cmd.append('--compressed')
        cmd.append('/sdcard/kwai-state.xml')
        try:
            p=adb(*cmd,timeout=18)
            q=adb('exec-out','cat','/sdcard/kwai-state.xml',timeout=18)
            if '<hierarchy' in q.stdout:
                path=f'{tag}.xml'
                open(path,'w',encoding='utf-8').write(q.stdout)
                return q.stdout
        except Exception:
            pass
        time.sleep(1)
    return ''

def nodes(xml):
    try:return list(ET.fromstring(xml).iter('node'))
    except Exception:return []

def center(n):
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds') or '')
    if not m:return None
    a,b,c,d=map(int,m.groups())
    return (a+c)//2,(b+d)//2

def tap_node(n,name):
    p=center(n)
    if not p:return False
    adb('shell','input','tap',str(p[0]),str(p[1]))
    log('ACTION='+name)
    time.sleep(max(1.5,SETTLE))
    return True

def rid(n):return (n.get('resource-id') or '').split('/')[-1]
def label(n):return ((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip().casefold()

def find_id(ns,*ids):
    for wanted in ids:
        for n in ns:
            if rid(n)==wanted and center(n):return n
    return None

def find_label(ns,*labels):
    ls={x.casefold() for x in labels}
    for n in ns:
        if label(n) in ls and center(n):return n
    return None

def login_surface(ns):
    # Existing explicit chooser / credential form identifiers.
    ids={rid(n) for n in ns}
    if any(x in ids for x in ('login_platform_expand_text','login_platform_item_layout')):
        return True
    edits=[n for n in ns if (n.get('class') or '').endswith('EditText')]
    if edits:
        ctx=' '.join(label(n)+' '+rid(n).casefold() for n in ns)
        if re.search(r'login|sign in|password|email|phone|telefone|senha|verification|code|c[oó]digo',ctx,re.I):return True
    return False

def handle_permission(ns):
    ids={rid(n) for n in ns}
    if 'permission_deny_button' not in ids and 'permission_allow_button' not in ids:return False
    prefer_allow=MODE in {'allow-permissions','allow-then-retry'}
    target=find_id(ns,'permission_allow_button') if prefer_allow else find_id(ns,'permission_deny_button')
    if target is None: target=find_id(ns,'permission_deny_button','permission_allow_button')
    return tap_node(target,'permission_'+('allow' if prefer_allow else 'deny')) if target is not None else False

def handle_known(ns):
    # Interest onboarding seen in prior failures.
    n=find_id(ns,'bt_interest_skip_top_right')
    if n is not None:return tap_node(n,'skip_interests')
    # Exact Kwai first-run continuation observed in prior runs.
    n=find_id(ns,'signin_fre_continue_button')
    if n is not None:return tap_node(n,'signin_fre_continue')
    if handle_permission(ns):return True
    # Expanded/collapsed native provider chooser.
    n=find_id(ns,'login_platform_expand_text')
    if n is not None:return tap_node(n,'expand_login_platforms')
    return False

def tap_home_login(ns):
    # Strongest observed signal: same resource id also labels For you, so match exact label first.
    for n in ns:
        if rid(n)=='irb_radioButton' and label(n) in {'log in','login','sign in','entrar','fazer login'} and center(n):
            return tap_node(n,'home_login_exact')
    n=find_label(ns,'log in','login','sign in','entrar','fazer login','log in / sign up','log in or sign up')
    if n is not None:return tap_node(n,'home_login_label')
    # Fallback observed geometry: left/top tab, never arbitrary content.
    cand=[]
    for n in ns:
        if rid(n)=='irb_radioButton' and center(n):
            x,y=center(n)
            if x<260 and y<420:cand.append(n)
    if cand:return tap_node(cand[0],'home_login_left_tab')
    return False

def maybe_prepare(ns):
    if MODE=='dismiss-guide':
        if find_id(ns,'guide_layout') is not None:
            adb('shell','input','swipe','540','1700','540','850','250'); log('ACTION=dismiss_guide_swipe'); time.sleep(2)
    elif MODE=='pregrant-notification':
        adb('shell','pm','grant','com.kwai.video','android.permission.POST_NOTIFICATIONS'); log('ACTION=pregrant_notification')
    elif MODE=='network-wait':
        adb('shell','svc','wifi','enable'); adb('shell','svc','data','enable')
        for i in range(5):
            p=adb('shell','ping','-c','1','-W','1','8.8.8.8',timeout=4)
            if p.returncode==0:log('NETWORK_READY=1');break
            time.sleep(2)
    elif MODE=='relaunch-before-login':
        relaunch(); log('ACTION=relaunch_before_login')
    return ns

# Install/launch through the already-proven path.
p=run('bash','kwai_vault_install.sh',timeout=300)
print(p.stdout,end='')
if p.returncode!=0:
    log('FAIL_INSTALL_OR_INITIAL_LAUNCH='+str(p.returncode));sys.exit(p.returncode)
adb('shell','svc','wifi','enable'); adb('shell','svc','data','enable')
time.sleep(max(2,SETTLE))

relaunch_budget=2
login_clicks=0
for step in range(18):
    xml=dump_xml(f'home-login-{step}')
    if not xml:
        log(f'STEP={step} UI_DUMP_FAIL=1')
        if relaunch_budget:
            relaunch_budget-=1; relaunch(); log('ACTION=relaunch_after_dump_fail'); continue
        break
    ns=nodes(xml)
    ids={rid(n) for n in ns}
    log(f'STEP={step} NODE_COUNT={len(ns)} PID='+(adb('shell','pidof','com.kwai.video').stdout.strip() or 'none'))
    if login_surface(ns):
        log('KWAI_HOME_LOGIN_SURFACE=PASS')
        sys.exit(0)
    # Android/Google interstitial: return home and relaunch Kwai, never click account/security UI.
    focus=adb('shell','dumpsys','window','windows').stdout
    if 'com.google.android.setupwizard' in focus:
        log('SETUPWIZARD_STOLE_FOREGROUND=1')
        adb('shell','input','keyevent','KEYCODE_HOME'); time.sleep(1); relaunch(); continue
    # Always clear explicit app/system gates first.
    if handle_known(ns):continue
    if step==0:maybe_prepare(ns); xml=dump_xml(f'home-login-{step}-prepared'); ns=nodes(xml) if xml else ns
    # Direct Home Log In route proved present in failed artifacts.
    if tap_home_login(ns):
        login_clicks+=1
        continue
    # If a click bounced back to Home, retry it after a relaunch depending on mode.
    if login_clicks and MODE in {'deny-then-retry','allow-then-retry','relaunch-after-login'} and relaunch_budget:
        relaunch_budget-=1; relaunch(); log('ACTION=relaunch_after_login_bounce'); continue
    # Last bounded fallback: Profile tab, then known dialog handling, then Login.
    if MODE=='profile-fallback':
        n=find_id(ns,'id_home_bottom_tab_me')
        if n is not None and tap_node(n,'profile_fallback'):continue
    # If process died, relaunch; otherwise give dynamic UI one more settle interval.
    if not adb('shell','pidof','com.kwai.video').stdout.strip() and relaunch_budget:
        relaunch_budget-=1; relaunch(); log('ACTION=relaunch_after_pid_loss'); continue
    time.sleep(max(1,SETTLE))

adb('shell','dumpsys','activity','activities').stdout and open('kwai-home-login-activities.txt','w').write(adb('shell','dumpsys','activity','activities').stdout)
open('kwai-home-login-window.txt','w').write(adb('shell','dumpsys','window','windows').stdout)
open('kwai-home-login-logcat.txt','w').write(adb('logcat','-d','-v','brief').stdout[-60000:])
log('LOGIN_CLICKS='+str(login_clicks))
log('KWAI_HOME_LOGIN_SURFACE=FAIL')
sys.exit(31)
