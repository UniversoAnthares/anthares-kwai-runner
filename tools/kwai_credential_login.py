#!/usr/bin/env python3
import os,re,subprocess,time,xml.etree.ElementTree as ET

LOGIN=os.environ.get('KWAI_LOGIN','')
PASSWORD=os.environ.get('KWAI_PASSWORD','')
if not LOGIN or not PASSWORD: raise SystemExit(2)

def adb(*args):
    return subprocess.run(['adb',*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=20).stdout

def snap():
    adb('shell','uiautomator','dump','/sdcard/kwai-cred.xml')
    xml=adb('exec-out','cat','/sdcard/kwai-cred.xml')
    return list(ET.fromstring(xml).iter('node'))

def txt(n): return ((n.get('text') or '')+' '+(n.get('content-desc') or '')+' '+(n.get('resource-id') or '')).strip().lower()
def bounds(n):
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds') or '')
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups()); return ((x1+x2)//2,(y1+y2)//2)
def tap(n):
    p=bounds(n)
    if not p:return False
    adb('shell','input','tap',str(p[0]),str(p[1]));time.sleep(1);return True

def edits(ns): return [n for n in ns if (n.get('class') or '').endswith('EditText') or n.get('editable')=='true']
def is_password(n): return n.get('password')=='true' or 'password' in txt(n) or 'senha' in txt(n)
def clear_and_type(n,value):
    if not tap(n): return False
    adb('shell','input','keyevent','KEYCODE_MOVE_END')
    for _ in range(160): adb('shell','input','keyevent','KEYCODE_DEL')
    safe=value.replace('%','%25').replace(' ','%s').replace('&','\\&').replace('(','\\(').replace(')','\\)')
    adb('shell','input','text',safe);time.sleep(1);return True

def exact_button(ns,words):
    pats={w.casefold() for w in words}
    c=[]
    for n in ns:
        t=((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip().casefold()
        if t in pats and bounds(n): c.append(n)
    return c[-1] if c else None

def challenge(ns):
    t=' '.join(txt(n) for n in ns)
    if any(x in t for x in ('verification code','enter code','code sent','código de verificação','digite o código','verify it\'s you','verify its you','captcha')): return True
    return False

def wait_password_or_challenge(seconds=12):
    for _ in range(seconds*2):
        ns=snap()
        if challenge(ns): return 'challenge',ns
        es=edits(ns)
        if any(is_password(n) for n in es): return 'password',ns
        time.sleep(.5)
    return 'stuck',snap()

# Enter native email/phone surface using the proven selector helper.
r=subprocess.run(['python3','tools/kwai_android_login_entry.py','auto']).returncode
if r == 3:
    # Native chooser is absent on fresh installs; recover by semantic navigation.
    recovered=subprocess.run(['python3','tools/kwai_login_surface_recovery.py']).returncode
    if recovered == 0:
        r=subprocess.run(['python3','tools/kwai_android_login_entry.py','auto']).returncode
if r != 0:
    print('KWAI_CREDENTIAL_METHOD_NOT_READY'); raise SystemExit(3)
ns=snap(); es=edits(ns)
if not es: print('KWAI_EMAIL_FIELD_MISSING'); raise SystemExit(3)
# Email screen should contain a non-password field.
email_field=next((n for n in es if not is_password(n)),None)
if email_field is None:
    print('KWAI_ACCOUNT_FIELD_NOT_VERIFIED')
    raise SystemExit(3)
if not clear_and_type(email_field,LOGIN): raise SystemExit(3)
ns=snap(); b=exact_button(ns,('Next','Continue','Avançar','Continuar'))
if b: tap(b)
else: adb('shell','input','keyevent','KEYCODE_ENTER');time.sleep(1)
state,ns=wait_password_or_challenge()
if state=='challenge': print('KWAI_LOGIN_CHALLENGE_AFTER_ACCOUNT'); raise SystemExit(6)
if state!='password': print('KWAI_ACCOUNT_STEP_DID_NOT_ADVANCE'); raise SystemExit(3)

es=edits(ns); verified=[n for n in es if is_password(n)]
if len(verified)!=1:
    print('KWAI_PASSWORD_FIELD_NOT_VERIFIED')
    raise SystemExit(4)
if not clear_and_type(verified[0],PASSWORD): print('KWAI_PASSWORD_FIELD_MISSING'); raise SystemExit(4)
ns=snap(); b=exact_button(ns,('Log in','Login','Sign in','Entrar','Continue','Continuar','Next','Avançar'))
if b: tap(b)
else: adb('shell','input','keyevent','KEYCODE_ENTER');time.sleep(1)

# Return success only after credential fields disappear. Challenges are explicit.
for _ in range(20):
    ns=snap()
    if challenge(ns): print('KWAI_POST_PASSWORD_CHALLENGE'); raise SystemExit(6)
    es=edits(ns); t=' '.join(txt(n) for n in ns)
    if not es and not any(x in t for x in ('enter your email address','password','senha')):
        print('KWAI_CREDENTIAL_LOGIN_SUBMITTED'); raise SystemExit(0)
    if any(x in t for x in ('incorrect password','wrong password','senha incorreta')):
        print('KWAI_LOGIN_REJECTED'); raise SystemExit(5)
    time.sleep(1)
print('KWAI_CREDENTIAL_FORM_STILL_VISIBLE'); raise SystemExit(7)
