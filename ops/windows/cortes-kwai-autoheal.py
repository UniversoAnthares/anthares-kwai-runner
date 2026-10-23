from __future__ import annotations
import datetime as dt, json, os, pathlib, re, subprocess, sys, time
ROOT=pathlib.Path(r'D:\AntharsWork\quota-write-20261017')
BASE=pathlib.Path(r'D:\AntharsWork\AntharesRemote')
PAUSE=ROOT/'.state'/'cortes-publisher-maintenance.pause'
LOG=BASE/'cortes-kwai-autoheal.log'
EVENTS=ROOT/'.state'/'kwai-physical-queue.log'
HEALTH=ROOT/'.state'/'android-device-health.json'
ADB=r'C:\Users\Lucas\.kwai-up\platform-tools\adb.exe'
PY=r'C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe'
AUTH=ROOT/'kwai-up'/'kwai_up_safe.py'
CREATE_NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)
def log(v):
    s=dt.datetime.now(dt.timezone.utc).isoformat()+' '+v
    LOG.parent.mkdir(parents=True,exist_ok=True)
    if LOG.exists() and LOG.stat().st_size>900000:
        LOG.write_text('\n'.join(LOG.read_text(encoding='utf-8').splitlines()[-180:])+'\n',encoding='utf-8')
    with LOG.open('a',encoding='utf-8') as f:f.write(s+'\n')
    print(s,flush=True)
def run(args,env=None,timeout=50):
    return subprocess.run(args,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout,creationflags=CREATE_NO_WINDOW)
def pending_worker():
    if not EVENTS.exists():return False
    rows=EVENTS.read_text(encoding='utf-8',errors='replace').splitlines()[-120:]
    work={}
    for row in rows:
        m=re.search(r'\bJOB_(START|OK|FAILED|ACK_REPAIRED)\s+(\S+)',row)
        if m:work[m.group(2)]=m.group(1)=='START'
    return any(work.values())
def check_connection(serial,port):
    env=os.environ.copy(); env['ADB_SERVER_SOCKET']=f'tcp:127.0.0.1:{port}'
    rows=run([ADB,'-P',str(port),'devices','-l'],env,25)
    if rows.returncode!=0 or not re.search(re.escape(serial)+r'\s+device\b',rows.stdout):return False
    try:
        code=run([ADB,'-P',str(port),'-s',serial,'shell','curl','-m','10','-s','-o','/dev/null','-w','%{http_code}','https://www.google.com/generate_204'],env,25)
        return code.returncode==0 and code.stdout.strip()=='204'
    except (OSError,subprocess.TimeoutExpired):return False
def auth(serial,port,package,check_only=False):
    if not check_connection(serial,port):return False
    if check_only:return True
    env=os.environ.copy()
    env.update(ADB_SERVER_SOCKET=f'tcp:127.0.0.1:{port}',ADB_SERVER_PORT=str(port),ADB_VENDOR_KEYS=r'C:\Users\Lucas\.android',
      KWAI_UP_ADB_SERIAL=serial,KWAI_UP_PACKAGE=package,KWAI_UP_EXPECTED_ACCOUNT='lucasrosalem',
      KWAI_UP_ARTIFACT_DIR=str(ROOT/'.state'/'kwai-autoheal-evidence'),
      PATH=str(pathlib.Path(ADB).parent)+os.pathsep+env.get('PATH',''))
    try:
        test=run([PY,str(AUTH),'auth'],env,115)
        return test.returncode==0 and 'KWAI_UP_STATE=AUTHENTICATED_IDENTITY ACCOUNT=lucasrosalem' in test.stdout
    except (OSError,subprocess.TimeoutExpired):return False
def recover_health():
    try:
        d=json.loads(HEALTH.read_text(encoding='utf-8'))
        if not isinstance(d,dict):return
        ph=d.get('physical_android',{})
        if isinstance(ph,dict):
            ph.update(consecutive_failures=0,degraded=False,last_failure_class='',last_verified_recovery_at=int(time.time()))
            tmp=HEALTH.with_suffix('.autoheal.tmp')
            tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
            os.replace(tmp,HEALTH)
    except Exception as e:log('HEALTH_STATE_WRITE_FAILED='+type(e).__name__)
def main():
    # Never clear a recovery pause while a dated platform ceiling is reached.
    floorpath=ROOT/'.state'/'kwai-daily-cap-owner-confirmed.json'
    try:
        if floorpath.exists():
            row=json.loads(floorpath.read_text(encoding='utf-8'))
            if row.get('schema')!='cortes.daily-owner-floor.v1':
                return log('HOLD_QUOTA_SCHEMA_UNVERIFIED')
            current=dt.datetime.now().astimezone().date().isoformat()
            floor=row.get('per_target_per_day',{}).get('kwai:lucasrosalem',{}).get(current,0)
            if type(floor)!=int or floor<0:return log('HOLD_QUOTA_INVALID')
            if floor>=100:
                return log('HOLD_DAILY_CAP_OWNER_CONFIRMED day='+current)
    except (OSError,ValueError,TypeError):
        return log('HOLD_QUOTA_UNREADABLE')
    if not PAUSE.exists():return log('ACTIVE_NO_PAUSE') if '--check' in sys.argv else None
    reason=PAUSE.read_text(encoding='utf-8-sig',errors='replace')
    if any(k in reason.upper() for k in ('DO_NOT_AUTO_RESUME','SECURITY_HOLD','MANUAL_LOCK')):
        return log('HOLD_MANUAL_OR_SECURITY')
    if not ('AUTO_RECOVERY_ALLOWED' in reason or 'Canary' in reason):
        return log('HOLD_UNKNOWN_REASON')
    age=time.time()-PAUSE.stat().st_mtime
    if age<600:return log('HOLD_RECENT_PAUSE')
    if pending_worker():return log('HOLD_INFLIGHT_WORK')
    dry='--check' in sys.argv
    if auth('993fce720408',5038,'kwai.lite.video',dry):
        mode='physical'
    elif auth('127.0.0.1:21543',5037,'com.kwai.video',dry):
        mode='memu'
    else:
        return log('HOLD_BOTH_IDENTITIES_OR_NETWORK_UNVERIFIED')
    if dry:return log('CHECK_OK_'+mode)
    if mode=='physical':recover_health()
    archive=PAUSE.with_name(PAUSE.name+'.recovered-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S'))
    try:os.replace(PAUSE,archive)
    except FileNotFoundError:return log('ALREADY_RELEASED')
    log('AUTO_RESUME_GATED_ACCOUNT_NETWORK_VERIFIED='+mode)
if __name__=='__main__':
    try:main()
    except Exception as exc:log('ERROR_'+type(exc).__name__)

