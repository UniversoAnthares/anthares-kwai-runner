#!/usr/bin/env python3
import os,re,subprocess,time,xml.etree.ElementTree as ET

LOGIN=os.environ.get('KWAI_LOGIN','')
PASSWORD=os.environ.get('KWAI_PASSWORD','')
if not LOGIN or not PASSWORD: raise SystemExit(2)

def adb(*args):
    return subprocess.run(['adb',*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=20).stdout

def snap():
    for _ in range(3):
        try:
            adb('shell','uiautomator','dump','/sdcard/kwai-cred.xml')
            xml=adb('exec-out','cat','/sdcard/kwai-cred.xml')
            if '<hierarchy' in xml:
                return list(ET.fromstring(xml).iter('node'))
        except Exception:
            pass
        time.sleep(1)
    raise SystemExit(3)

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
    for _ in range(min(160,len(n.get('text') or '')+8) if (n.get('text') or '') else 0): adb('shell','input','keyevent','KEYCODE_DEL')
    safe=value.replace('%','%25').replace(' ','%s').replace('&','\\&').replace('(','\\(').replace(')','\\)')
    adb('shell','input','text',safe);time.sleep(1);return True

def exact_button(ns,words):
    pats={w.casefold() for w in words}
    c=[]
    for n in ns:
        t=((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip().casefold()
        if t in pats and bounds(n): c.append(n)
    return c[-1] if c else None

def safe_form_inventory(ns,stage):
    """Resource and control semantics only: never print field text or credentials."""
    known=('next','continue','login','log in','sign in','submit','send','code','password','email','phone','check','agree','entrar','avançar','continuar','senha','verifica','confirmar','obter','enviar')
    fields=edits(ns)
    print('KWAI_FORM_%s_FIELDS=%d' % (stage,len(fields)),flush=True)
    for i,n in enumerate(fields[:5]):
        print('KWAI_FORM_%s_FIELD_%d=type:%s password:%s enabled:%s clickable:%s id:%s' %
            (stage,i,(n.get('class') or '').split('.')[-1],n.get('password'),n.get('enabled'),n.get('clickable'),(n.get('resource-id') or '')[-90:]),flush=True)
    count=0
    for n in ns:
        label=((n.get('text') or '')+' '+(n.get('content-desc') or '')).strip().casefold()
        rid=(n.get('resource-id') or '').casefold()
        cls=(n.get('class') or '').split('.')[-1]
        if not bounds(n) or cls=='EditText':continue
        if not (n.get('clickable')=='true' or cls in ('Button','CheckBox','TextView')):continue
        relevant=next((w.replace(' ','_') for w in known if w in label or w in rid),None)
        if not relevant:continue
        print('KWAI_FORM_%s_CTL_%d=kind:%s id:%s enabled:%s clickable:%s checked:%s class:%s' %
            (stage,count,relevant,rid[-85:],n.get('enabled'),n.get('clickable'),n.get('checked'),cls),flush=True)
        count+=1
        if count>=24:break

def find_semantic_control(ns,words):
    target=tuple(w.casefold() for w in words)
    choices=[]
    for n in ns:
        idstr=(n.get('resource-id') or '').casefold()
        label=((n.get('text') or '')+' '+(n.get('content-desc') or '')).casefold()
        if not bounds(n) or n.get('enabled')=='false':continue
        if any(w in label or w in idstr for w in target):
            p=bounds(n)
            choices.append((int(n.get('clickable')=='true'),int(n.get('class','').endswith('Button')),p[1],n))
    return sorted(choices,key=lambda x:(x[0],x[1],x[2]),reverse=True)[0][-1] if choices else None

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

# The previous deep-link/component recovery path was structurally unreliable.
# First reach the native Home -> Log In surface through the proven state machine,
# then select the actual email/phone method without touching third-party OAuth UI.
env=os.environ.copy()
env.setdefault('KWAI_LOGIN_MODE','plain')
env.setdefault('KWAI_LOGIN_SETTLE','3')
r=subprocess.run(['python3','tools/kwai_home_login_state_machine.py'],env=env).returncode
if r != 0:
    print('KWAI_HOME_LOGIN_STATE_MACHINE_FAILED'); raise SystemExit(3)
digits=re.sub(r'\\D','',LOGIN)
login_kind='email' if '@' in LOGIN else ('phone' if len(digits)>=8 else 'other')
print('KWAI_LOGIN_IDENTIFIER_KIND='+login_kind)
chosen='phone' if login_kind=='phone' else 'email'
r=subprocess.run(['python3','tools/kwai_android_login_entry.py',chosen],env=env).returncode
if r != 0:
    print('KWAI_CREDENTIAL_METHOD_NOT_READY'); raise SystemExit(3)

ns=snap(); es=edits(ns)
if not es: print('KWAI_EMAIL_FIELD_MISSING'); raise SystemExit(3)
email_field=next((n for n in es if not is_password(n)),None)
if email_field is None:
    print('KWAI_ACCOUNT_FIELD_NOT_VERIFIED')
    raise SystemExit(3)
if not clear_and_type(email_field,LOGIN): raise SystemExit(3)
ns=snap()
typed=any(LOGIN.casefold() in (n.get('text') or '').casefold() for n in edits(ns))
print('KWAI_ACCOUNT_INPUT_COMMITTED='+str(typed),flush=True)
safe_form_inventory(ns,'WITH_KEYBOARD')
# Dismiss Android soft keyboard before choosing the native continuation control.
adb('shell','input','keyevent','KEYCODE_BACK'); time.sleep(1)
ns=snap()
safe_form_inventory(ns,'AFTER_IME_DISMISS')
continue_labels=('Next','Continue','Avançar','Continuar','Log in','Login','Sign in','Entrar','Send code','Get code','Submit','Use password')
b=exact_button(ns,continue_labels) or find_semantic_control(ns,('btn_next','next_button','submit','continue','send_code','get_code','login_button','email_next','sendcode'))
print('KWAI_ACCOUNT_CONTINUE_PRESENT='+str(b is not None))
if b is not None and b.get('enabled')!='false':
    tap(b)
else:
    adb('shell','input','keyevent','KEYCODE_ENTER');time.sleep(2)
state,ns=wait_password_or_challenge()
if state=='challenge': print('KWAI_LOGIN_CHALLENGE_AFTER_ACCOUNT'); raise SystemExit(6)
if state=='stuck':
    safe_form_inventory(ns,'AFTER_NATIVE_NEXT')
    visible=' '.join(((n.get('text') or '')+' '+(n.get('content-desc') or '')).casefold() for n in ns)
    for key,terms in (
        ('INVALID_ACCOUNT',('invalid email','invalid address','email is invalid','endereço inválido')),
        ('ACCOUNT_NOT_FOUND',('account not found','no account','account does not exist','conta inexistente')),
        ('AUTH_NETWORK_FAILURE',('network error','network unavailable','connection failed','try again later','erro de rede')),
        ('EXCESSIVE_ATTEMPTS',('too many attempts','try again tomorrow','many requests','muitas tentativas')),
    ):
        if any(t in visible for t in terms):
            print('KWAI_ACCOUNT_NEXT_FAILURE='+key,flush=True)
            raise SystemExit(7)
    # Some builds keep the suggestion layer over Next after the IME closes.
    # Try the native keyboard submit action without changing the identifier.
    print('KWAI_ACCOUNT_NEXT_RECOVERY=IME_SUBMIT',flush=True)
    adb('shell','input','keyevent','KEYCODE_ENTER')
    state,ns=wait_password_or_challenge(5)
    if state=='stuck':
        safe_form_inventory(ns,'AFTER_IME_SUBMIT')
        print('KWAI_ACCOUNT_NEXT_RECOVERY=DIRECT_BUTTON_RETRY',flush=True)
        candidate=find_semantic_control(ns,('btn_next','next_button'))
        if candidate is not None and candidate.get('enabled')!='false':
            tap(candidate)
            state,ns=wait_password_or_challenge(5)
        if state=='stuck':safe_form_inventory(ns,'AFTER_DIRECT_RETRY')
if state!='password':
    # Some builds require choosing password login explicitly from the account step.
    alt=exact_button(ns,('Use password','Log in with password','Login with password','Entrar com senha','Password login','Other methods'))
    print('KWAI_PASSWORD_LOGIN_OPTION_PRESENT='+str(bool(alt)))
    if alt is not None:
        tap(alt)
        state,ns=wait_password_or_challenge(8)
    if state=='challenge': print('KWAI_LOGIN_CHALLENGE_AFTER_ACCOUNT'); raise SystemExit(6)
if state!='password': print('KWAI_ACCOUNT_STEP_DID_NOT_ADVANCE'); raise SystemExit(3)

es=edits(ns); verified=[n for n in es if is_password(n)]
if len(verified)!=1:
    print('KWAI_PASSWORD_FIELD_NOT_VERIFIED')
    raise SystemExit(4)
if not clear_and_type(verified[0],PASSWORD): print('KWAI_PASSWORD_FIELD_MISSING'); raise SystemExit(4)
ns=snap(); b=exact_button(ns,('Log in','Login','Sign in','Entrar','Continue','Continuar','Next','Avançar'))
if b is not None: tap(b)
else: adb('shell','input','keyevent','KEYCODE_ENTER');time.sleep(1)

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
