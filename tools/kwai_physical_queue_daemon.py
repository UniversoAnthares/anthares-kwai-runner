#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,os,pathlib,re,socket,subprocess,sys,time,urllib.error,urllib.request
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding
from android_adb_inventory import online_devices
from cortes_neon_queue_adapter import signed_legacy_queue_call
from android_device_adapters import ensure_memu_transport

ROOT=pathlib.Path(__file__).resolve().parents[1]
CONTROL=os.getenv('ANTHARES_CONTROL_URL','https://anthares-control.anthares1.workers.dev').rstrip('/')
EXECUTOR='physical_android'; MODEL='M2004J19C'; EXPECTED_ACCOUNT=os.getenv('KWAI_EXPECTED_ACCOUNT','lucasrosalem').lstrip('@').lower()
PYTHON=os.getenv('ANTHARES_PYTHON',sys.executable)
ADB=os.getenv('ANTHARES_ADB',r'C:\Users\Lucas\.kwai-up\platform-tools\adb.exe')
ADB_KEYS=os.getenv('ADB_VENDOR_KEYS',r'C:\Users\Lucas\.android')
PRIVATE_KEY=pathlib.Path(os.getenv('ANTHARES_PHYSICAL_EXECUTOR_KEY',r'D:\AntharesWork\anthares-clipper\local-control\executor-private-current.pem'))
STATE_DIR=ROOT/'.state' if EXPECTED_ACCOUNT=='lucasrosalem' else ROOT/'.state'/'kwai-secondary'
WORKER=ROOT/'tools'/'kwai_device_failover_worker.py'; ACK=STATE_DIR/'android-publish-ack.json'; PUBSTATE=ROOT/'.state'/'kwai-native-cortes'
LOGDIR=STATE_DIR; LOG=LOGDIR/'kwai-physical-queue.log'; LOCK=LOGDIR/'kwai-physical-queue.lock'; MAINTENANCE=ROOT/'.state'/'cortes-publisher-maintenance.pause'
TTL=3600; POLL=20; EMPTY_POLL=180
LAST_QUEUE_EMPTY=False
LAST_NETWORK_BAD=False
WP_PENDING=LOGDIR/'cortes-wp-callback-pending.json'

# Schedule de publicação: distribui cortes uniformemente entre o primeiro envio e 23h,
# recalculando os intervalos conforme os cortes restantes, com limite de 100 vídeos/conta/dia.
SCHEDULE_FILE=LOGDIR/'kwai-publication-schedule.json'
CUT_ATTEMPTS_FILE=LOGDIR/'kwai-cut-attempts.json'
PHYSICAL_DEVICE_LOCK=ROOT/'.state'/'kwai-physical-device.lock'
PHYSICAL_DEVICE_EXCLUSIVE=int(os.getenv('ANTHARES_KWAI_PHYSICAL_PRIMARY_EXCLUSIVE','0'))
LAST_PUBLISH_LOGGED=''
_SCHEDULE_CACHE={'mtime':0,'data':{}}
_CUT_ATTEMPTS_CACHE={'mtime':0,'data':{}}
_PHYSICAL_DEVICE_OWNER=None
_PHYSICAL_DEVICE_OWNER_AT=0

# Persistent preflight circuit breaker: avoid re-leasing the same work every 20s
# when Android authentication or both approved executors are unavailable.
RETRY_GATE=LOGDIR/'kwai-preflight-retry-not-before.json'
LAST_RETRY_NOTICE=''
def retry_gate_active():
 global LAST_RETRY_NOTICE
 try: d=json.loads(RETRY_GATE.read_text(encoding='utf-8'))
 except FileNotFoundError:return False
 except (OSError,ValueError) as e:
  log('KWAI_PREFLIGHT_RETRY_GATE_INVALID priority=P0 no_lease=1')
  return True
 if d.get('schema')!='cortes.kwai.preflight.backoff.v1':
  log('KWAI_PREFLIGHT_RETRY_GATE_BAD_SCHEMA priority=P0 no_lease=1')
  return True
 try: left=int(d['not_before_epoch'])-int(time.time())
 except (KeyError,TypeError,ValueError):
  log('KWAI_PREFLIGHT_RETRY_GATE_BAD_TIME priority=P0 no_lease=1')
  return True
 if left<=0:return False
 token=str(d['not_before_epoch'])
 if LAST_RETRY_NOTICE!=token:
  log('KWAI_PREFLIGHT_BACKOFF no_lease=1 remaining_seconds='+str(left)+' reason='+str(d.get('reason','unknown'))[:55])
  LAST_RETRY_NOTICE=token
 return True
def arm_preflight_backoff(code,precommit_timeout=False):
 # A proven PRE-COMMIT transport timeout may be retried after a short cooling
 # period, preserving the central 23h pacing gate and anti-duplicate lease.
 # Authentication/security/media conflicts retain the existing longer fence.
 seconds=180 if precommit_timeout else (1800 if int(code)==81 else 900)
 until=int(time.time())+seconds
 payload={'schema':'cortes.kwai.preflight.backoff.v1','not_before_epoch':until,
          'reason':'precommit_transport_timeout' if precommit_timeout else 'worker_exit_'+str(code),
          'created_epoch':int(time.time())}
 RETRY_GATE.parent.mkdir(parents=True,exist_ok=True)
 tmp=RETRY_GATE.with_suffix('.tmp')
 tmp.write_text(json.dumps(payload),encoding='utf-8')
 tmp.replace(RETRY_GATE)
 log('KWAI_PREFLIGHT_BACKOFF_ARMED no_lease=1 retry_seconds='+str(seconds)+' priority=P0 rc='+str(code))

# Minimum real-world posts attested by the owner when remote proof/ledger diverge.
# Each calendar day is independent: an override from yesterday cannot block tomorrow.
DAILY_OWNER_FLOOR=ROOT/'.state'/'kwai-daily-cap-owner-confirmed.json'
LAST_OWNER_CAP_LOGGED=''
def owner_daily_floor():
 import datetime
 day=datetime.datetime.now().astimezone().date().isoformat()
 try:
  record=json.loads(DAILY_OWNER_FLOOR.read_text(encoding='utf-8'))
 except FileNotFoundError:return (day,0)
 except (OSError,ValueError) as exc:raise RuntimeError('daily_owner_floor_unreadable') from exc
 if record.get('schema')!='cortes.daily-owner-floor.v1':raise RuntimeError('daily_owner_floor_schema_invalid')
 value=record.get('per_target_per_day',{}).get('kwai:'+EXPECTED_ACCOUNT,{}).get(day,0)
 if type(value)!=int or value<0:raise RuntimeError('daily_owner_floor_invalid')
 return day,value
def owner_cap_reached():
 global LAST_OWNER_CAP_LOGGED,LAST_QUEUE_EMPTY
 day,floor=owner_daily_floor()
 limit=max(1,min(100,int(os.getenv('CORTES_KWAI_DAILY_POST_LIMIT','100'))))
 if floor>=limit:
  if LAST_OWNER_CAP_LOGGED!=day:
   log('KWAI_DAILY_CAP_BLOCKED source=owner_attested day='+day+' minimum='+str(floor)+' cap='+str(limit)+' no_lease=1 priority=P0')
   LAST_OWNER_CAP_LOGGED=day
  LAST_QUEUE_EMPTY=True
  return True
  return False

# --- Schedule de publicação uniforme entre primeiro envio e 23h ---
def _load_json_cache(path, cache):
  try:
    mtime=path.stat().st_mtime
  except FileNotFoundError:
    if cache['data'] is not None:
      cache['mtime']=0; cache['data']={}
    return {}
  if mtime==cache['mtime'] and cache['data'] is not None:
    return cache['data']
  try:
    data=json.loads(path.read_text(encoding='utf-8'))
  except (OSError,ValueError):
    data={}
  cache['mtime']=mtime; cache['data']=data
  return data

def _save_json(path, data):
  path.parent.mkdir(parents=True,exist_ok=True)
  tmp=path.with_suffix('.tmp')
  tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  tmp.replace(path)

def load_schedule():
  return _load_json_cache(SCHEDULE_FILE,_SCHEDULE_CACHE)

def save_schedule(data):
  _save_json(SCHEDULE_FILE,data)
  _SCHEDULE_CACHE['mtime']=SCHEDULE_FILE.stat().st_mtime
  _SCHEDULE_CACHE['data']=data

def load_cut_attempts():
  return _load_json_cache(CUT_ATTEMPTS_FILE,_CUT_ATTEMPTS_CACHE)

def save_cut_attempts(data):
  _save_json(CUT_ATTEMPTS_FILE,data)
  _CUT_ATTEMPTS_CACHE['mtime']=CUT_ATTEMPTS_FILE.stat().st_mtime
  _CUT_ATTEMPTS_CACHE['data']=data

def compute_schedule(posted_today, pending, cap, now=None, stats=None):
  """Independent v3 verification: actual confirmed post + remaining slots to 23h.

  The Neon lease gate is authoritative. A mismatched schedule fails closed.
  A same-day backlog refill recomputes intervals without arbitrary fixed delays.
  """
  import datetime
  if now is None:now=datetime.datetime.now().astimezone()
  if not stats or stats.get('pacing_version')!='kwai-public-post-proportional-06to23-v3':
    raise RuntimeError('kwai_pacing_version_unverified')
  if stats.get('target_key')!='kwai:'+EXPECTED_ACCOUNT:
    raise RuntimeError('kwai_pacing_account_mismatch')
  deadline=now.replace(hour=23,minute=0,second=0,microsecond=0)
  def parse_iso(value):
    if not value:return None
    x=datetime.datetime.fromisoformat(str(value).replace('Z','+00:00'))
    if not x.tzinfo:raise RuntimeError('kwai_pacing_timestamp_missing_timezone')
    return x.astimezone(now.tzinfo)
  server_deadline=parse_iso(stats.get('deadline_at'))
  if server_deadline is None or abs((server_deadline-deadline).total_seconds())>2:
    raise RuntimeError('kwai_pacing_deadline_mismatch')
  open_at=now.replace(hour=6,minute=0,second=0,microsecond=0)
  server_open=parse_iso(stats.get('window_open_at'))
  if server_open is None or abs((server_open-open_at).total_seconds())>2:
    raise RuntimeError('kwai_pacing_open_window_mismatch')
  posted=int(stats.get('confirmed_today',-1))
  used=int(stats.get('started_today',-1))
  remaining=min(pending,max(0,cap-used))
  if posted<0 or used<posted or used>100 or posted_today!=posted:
    raise RuntimeError('kwai_pacing_daily_usage_mismatch')
  if pending<0 or remaining<0 or remaining!=int(stats.get('remaining_today',-1)):
    raise RuntimeError('kwai_pacing_remaining_mismatch')
  first=parse_iso(stats.get('first_confirmed_at'))
  last=parse_iso(stats.get('last_confirmed_at'))
  entry={'posted':posted,'used':used,'remaining':remaining,
         'last_at':last.isoformat() if last else None,
         'first_at':first.isoformat() if first else None,
         'deadline':deadline.isoformat(),
         'pacing_version':'kwai-public-post-proportional-06to23-v3'}
  if now<open_at:
    entry.update({'interval':0,'next_at':open_at.isoformat(),'status':'WAIT_OPEN'})
  elif now>=deadline:
    entry.update({'interval':0,'next_at':None,'status':'BLOCKED_SAME_DAY_CAPACITY'})
  elif remaining<=0:
    entry.update({'interval':0,'next_at':None,'status':'BLOCKED_PLATFORM_LIMIT'})
  elif not last:
    if posted>0 or first is not None:raise RuntimeError('kwai_pacing_missing_first_post_clock')
    entry.update({'interval':0,'next_at':now.isoformat(),'status':'DUE'})
  else:
    if not first or first>last or last>now or last.date()!=now.date():
      raise RuntimeError('kwai_pacing_actual_publication_clock_invalid')
    interval=(deadline-last).total_seconds()/(remaining+1)
    if interval<=0:raise RuntimeError('kwai_pacing_bad_interval')
    due=last+datetime.timedelta(seconds=interval)
    actual=parse_iso(stats.get('next_due_at'))
    if not actual or abs((actual-due).total_seconds())>3:
      raise RuntimeError('kwai_pacing_server_due_diverges_from_math')
    entry.update({'interval':interval,'next_at':due.isoformat(),
                  'status':'DUE' if now>=due else 'WAIT'})
  if entry['status']!=stats.get('status'):
    raise RuntimeError('kwai_pacing_server_status_mismatch')
  day=now.date().isoformat()
  ledger=load_schedule()
  ledger[day]=entry
  save_schedule(ledger)
  return float(entry['interval']),entry

def next_cut_due(now=None):
  """Retorna o próximo horário agendado para corte, se houver."""
  import datetime
  if now is None:
    import datetime
    now=datetime.datetime.now().astimezone()
  schedule=load_schedule()
  day=now.date().isoformat()
  entry=schedule.get(day,{})
  next_at=entry.get('next_at')
  if not next_at:return None
  try:
    due=datetime.datetime.fromisoformat(next_at)
  except ValueError:
    return None
  if due<=now:return due
  return due

def record_published(jid, now=None):
  """Record operational ACK while preserving the canonical public-post anchor."""
  import datetime
  if now is None:now=datetime.datetime.now().astimezone()
  day=now.date().isoformat()
  entries=load_schedule()
  entry=entries.get(day,{})
  entry['last_ack_at']=now.isoformat()
  entry['last_ack_job_id']=jid
  entries[day]=entry
  save_schedule(entries)
  return None

def record_cut_attempt(source_id, scheduled_at=None, result='attempted'):
  """Registra tentativa de corte para impedir nova tentativa antes do horário previsto."""
  import datetime
  now=datetime.datetime.now().astimezone()
  attempts=load_cut_attempts()
  entry=attempts.get(source_id,{'attempts':0,'last_at':None,'next_allowed':None,'last_result':None})
  entry['attempts']=int(entry.get('attempts',0))+1
  entry['last_at']=now.isoformat()
  entry['last_result']=result
  if scheduled_at:
    entry['next_allowed']=scheduled_at
  else:
    next_dt=now+datetime.timedelta(seconds=int(os.getenv('CORTES_KWAI_MIN_RETRY_SECONDS','300')))
    entry['next_allowed']=next_dt.isoformat()
  attempts[source_id]=entry
  save_cut_attempts(attempts)
  return entry

def can_attempt_cut(source_id, now=None):
  """Verifica se o corte pode ser tentado (não antes do horário previsto)."""
  import datetime
  if now is None:now=datetime.datetime.now().astimezone()
  attempts=load_cut_attempts()
  entry=attempts.get(source_id)
  if not entry:return True,None
  next_allowed=entry.get('next_allowed')
  if not next_allowed:return True,None
  try:
    due=datetime.datetime.fromisoformat(next_allowed)
  except ValueError:
    return True,None
  if due<=now:return True,None
  return False,due

# --- Lock de exclusividade do Android físico ---
def acquire_physical_device_lock(owner):
  """Garante que somente um executor utilize o Android físico por vez."""
  global _PHYSICAL_DEVICE_OWNER,_PHYSICAL_DEVICE_OWNER_AT
  import time
  LOGDIR.mkdir(parents=True,exist_ok=True)
  try:
    fd=os.open(str(PHYSICAL_DEVICE_LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(fd,str(os.getpid()).encode())
    os.close(fd)
    _PHYSICAL_DEVICE_OWNER=owner
    _PHYSICAL_DEVICE_OWNER_AT=time.time()
    return True
  except FileExistsError:
    try:
      owner_text=PHYSICAL_DEVICE_LOCK.read_text(encoding='utf-8').strip()
      current_owner=owner_text.split(':')[0] if ':' in owner_text else owner_text
      if current_owner==owner:
        _PHYSICAL_DEVICE_OWNER=owner
        _PHYSICAL_DEVICE_OWNER_AT=time.time()
        return True
    except OSError:
      pass
    return False

def release_physical_device_lock(owner):
  global _PHYSICAL_DEVICE_OWNER,_PHYSICAL_DEVICE_OWNER_AT
  try:
    if PHYSICAL_DEVICE_LOCK.exists():
      PHYSICAL_DEVICE_LOCK.unlink()
  except OSError:
    pass
  if _PHYSICAL_DEVICE_OWNER==owner:
    _PHYSICAL_DEVICE_OWNER=None
    _PHYSICAL_DEVICE_OWNER_AT=0

def physical_device_locked_by(owner):
  global _PHYSICAL_DEVICE_OWNER,_PHYSICAL_DEVICE_OWNER_AT
  if _PHYSICAL_DEVICE_OWNER==owner:
    return True
  try:
    if not PHYSICAL_DEVICE_LOCK.exists():return False
    owner_text=PHYSICAL_DEVICE_LOCK.read_text(encoding='utf-8').strip()
    current_owner=owner_text.split(':')[0] if ':' in owner_text else owner_text
    return current_owner==owner
  except OSError:
    return False

_key=None

class QueueStorageBlocked(RuntimeError):
 pass

def queue_failure(op,code,data):
 if code==503 and data.get('error')=='queue_storage_quota_exhausted':
  raise QueueStorageBlocked('queue_storage_quota_exhausted')
 raise RuntimeError(f'queue-{op}:{code}:{data}')

_LAST_QA_DISPATCH=-99999999.0
def log(msg):
 LOGDIR.mkdir(parents=True,exist_ok=True); line=time.strftime('%Y-%m-%dT%H:%M:%S')+' '+msg; print(line,flush=True)
 try:
  with LOG.open('a',encoding='utf-8') as f:f.write(line+'\n')
 except OSError:pass
 # Fast path to QA; scheduled watchdog is the independent fallback.
 if re.search(r'JOB_FAILED|LOOP_ERROR|QUEUE_BLOCKED|PREFLIGHT_FAILED|QUEUE_FAIL_CALLBACK_ERROR|KWAI_ANDROID_DNS_PREFLIGHT_BLOCKED|JOB_ACK_PENDING|ACK_RECONCILE_PENDING|KWAI_PROOF_RECOVERY_FAILED|KWAI_PHYSICAL_SLEEP_BLOCKED',msg):
  global _LAST_QA_DISPATCH
  now=time.monotonic()
  if now-_LAST_QA_DISPATCH>=90:
   _LAST_QA_DISPATCH=now
   script=pathlib.Path(r'D:\AntharsWork\AntharesRemote\cortes-kwai-qa-p0-watchdog.ps1')
   if script.exists():
    try:subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',str(script)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except OSError:pass

def compact(d):return json.dumps(d,separators=(',',':'),ensure_ascii=False)
def key():
 global _key
 if _key is None:
  _key=serialization.load_pem_private_key(PRIVATE_KEY.read_bytes(),password=None)
 return _key
def signed_post(path,payload,timeout=30):
 # All /job operations are always fenced by the canonical Neon queue.
 if path.startswith('/job/'):
  return signed_legacy_queue_call(path,payload)
 raw=compact(payload).encode('utf-8'); ts=str(int(time.time())); message=(ts+'\nPOST\n'+path+'\n').encode()+raw
 sig=base64.b64encode(key().sign(message,padding.PKCS1v15(),hashes.SHA256())).decode('ascii')
 req=urllib.request.Request(CONTROL+path,data=raw,method='POST',headers={'Content-Type':'application/json','User-Agent':'AntharesPhysicalAndroid/1','X-Anthares-Executor-Timestamp':ts,'X-Anthares-Executor-Signature':sig})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r: body=r.read().decode('utf-8','replace'); code=r.status
 except urllib.error.HTTPError as e:
  body=e.read().decode('utf-8','replace'); code=e.code
 try:d=json.loads(body)
 except Exception:d={'ok':False,'error':'invalid-response','body':body[-500:]}
 return code,d

def qpost(op,payload):
 code,d=signed_post('/job/'+op,{'executor':EXECUTOR,**payload})
 if code//100!=2 or not d.get('ok'):queue_failure(op,code,d)
 return d

_PORT_CACHE={'port':'5037','until':0}
def physical_adb_port():
 # USB may belong to the shared ADB server on 5037 or dedicated 5038.
 if time.time()<_PORT_CACHE['until']:return _PORT_CACHE['port']
 env=os.environ.copy();env['ADB_VENDOR_KEYS']=ADB_KEYS
 for port in tuple(dict.fromkeys([os.getenv('ANTHARES_PHYSICAL_ADB_PORT','5037'),'5037'])):
  try:
   p=subprocess.run([ADB,'-P',port,'devices','-l'],capture_output=True,text=True,timeout=8,env=env,check=False)
   if p.returncode==0 and any(x.get('model')==MODEL for x in online_devices(p.stdout or '')):
    _PORT_CACHE.update(port=port,until=time.time()+60);return port
  except (OSError,subprocess.SubprocessError):pass
 _PORT_CACHE.update(port='5037',until=time.time()+12)
 return '5037'
def adb(*a,timeout=25,check=False):
 env=os.environ.copy(); env['ADB_VENDOR_KEYS']=ADB_KEYS
 return subprocess.run([ADB,'-P',physical_adb_port(),*a],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,check=check,env=env)
def devices():
 p=adb('devices','-l')
 return online_devices(p.stdout) if p.returncode==0 else []
def resolve_serial():
 for attempt in range(3):
  for d in devices():
   if d.get('model')==MODEL:return d['serial']
  if attempt<2:time.sleep(2)
 p=adb('mdns','services')
 for ep in re.findall(r'(\d{1,3}(?:\.\d{1,3}){3}:\d+)',p.stdout or ''):
  adb('connect',ep,timeout=20)
 for d in devices():
  if d.get('model')==MODEL:return d['serial']
 raise RuntimeError('physical-device-unavailable')
def preflight():
 try:
  s=resolve_serial(); state=adb('-s',s,'get-state').stdout.strip(); model=adb('-s',s,'shell','getprop','ro.product.model').stdout.strip(); pkg=adb('-s',s,'shell','pm','path','kwai.lite.video').stdout
  power=adb('-s',s,'shell','dumpsys','power',timeout=15).stdout or ''
  if 'mWakefulness=Asleep' in power:
   adb('-s',s,'shell','input','keyevent','224',timeout=12)
   time.sleep(2)
   if 'mWakefulness=Asleep' in (adb('-s',s,'shell','dumpsys','power',timeout=15).stdout or ''):
    adb('-s',s,'shell','/data/local/tmp/anthares-hid-tap.sh','540','1200',timeout=18)
    time.sleep(1)
   if 'mWakefulness=Asleep' in (adb('-s',s,'shell','dumpsys','power',timeout=15).stdout or ''):
    log('KWAI_PHYSICAL_SLEEP_BLOCKED no_lease=1 priority=P0')
    return False,s
  native=adb('-s',s,'shell','test','-x','/data/local/tmp/anthares-kwai-native.sh').returncode==0
  touch=adb('-s',s,'shell','test','-x','/data/local/tmp/anthares-hid-tap.sh').returncode==0
  return bool(state=='device' and model==MODEL and 'package:' in pkg and native and touch),s
 except Exception:return False,''
def network_ready(serial):
 # Read-only DNS and HTTPS gate; never lease work while Android cannot reach Kwai.
 try:
  p=adb('-s',serial,'shell','timeout','11','curl','-sS','-I','--connect-timeout','4','--max-time','8','https://www.kwai.com',timeout=16,check=False)
  return p.returncode==0 and bool(re.search(r'HTTP/[^ ]+ (?:200|301|302|303|307|308)',p.stdout or ''))
 except (OSError,subprocess.SubprocessError,ValueError):return False

def heartbeat(healthy,serial='',error=''):
 if os.getenv('CORTES_QUEUE_BACKEND','cloudflare').strip().lower()=='neon':
  return 202,{'ok':True,'backend':'vercel-neon','cloudflare_heartbeat_skipped':True}
 payload={'executor':EXECUTOR,'healthy':bool(healthy),'failures':0 if healthy else 1,'host':socket.gethostname(),'platform':'android','model':MODEL,'adb_serial':serial,'capabilities':['kwai'],'daily_limit':100,'expected_accounts':[EXPECTED_ACCOUNT]}
 if error:payload['last_error']=error[-300:]
 return signed_post('/heartbeat',payload)
def jobenv(job,serial):
 required=('id','lease_generation','source_id','source_start','source_end','video_url'); missing=[k for k in required if job.get(k) in (None,'')]
 if missing:raise RuntimeError('lease-missing:'+','.join(missing))
 account=str(job.get('expected_account') or job.get('account_id') or EXPECTED_ACCOUNT).lstrip('@').lower()
 if account!=EXPECTED_ACCOUNT:raise RuntimeError('unsupported-account:'+account)
 env=os.environ.copy(); port=physical_adb_port(); env['ANTHARES_PHYSICAL_ADB_PORT']=port; env['ADB_SERVER_PORT']=port; env['ADB_SERVER_SOCKET']='tcp:127.0.0.1:'+port; env.update({'ADB_VENDOR_KEYS':ADB_KEYS,'ANTHARES_ADB':ADB,'ANTHARES_PHYSICAL_ADB_SERIAL':serial,'KWAI_QUEUE_JOB_ID':str(job['id']),'KWAI_LEASE_OWNER':str(job.get('lease_owner') or ''),'KWAI_LEASE_GENERATION':str(job['lease_generation']),'KWAI_SOURCE_ID':str(job['source_id']),'KWAI_SOURCE_START':str(job['source_start']),'KWAI_SOURCE_END':str(job['source_end']),'KWAI_VIDEO_URL':str(job['video_url']),'KWAI_VIDEO_TITLE':str(job.get('video_title') or ''),'KWAI_EXPECTED_ACCOUNT':account})

 # Mark the primary as transport-ready, but identity verification remains in
 # kwai_up_safe.prepare() before STARTED. Never infer MEmu login readiness.
 env['ANTHARES_PHYSICAL_KWAI_AUTHENTICATED']='true' if serial else 'false'
 # The parent verifies MEmu only when physical preflight fails.
 # Preserve failover intent in the leased worker without relaxing its live identity gate.
 if not serial and env.get('ANTHARES_MEMU_KWAI_AUTHENTICATED')=='true':
  env['ANTHARES_KWAI_PHYSICAL_PRIMARY_EXCLUSIVE']='0'
  env['ANTHARES_KWAI_FORCE_MEMU']='1'
 env['ANTHARES_KWAI_CAPTION_OPTIONAL']='1'
 env['ANTHARES_ANDROID_ACK_STATE']=str(ACK)
 env['ANTHARES_ANDROID_HEALTH_STATE']=str(STATE_DIR/'android-device-health.json')
 env['ADB_SERVER_PORT']=port; env['ADB_SERVER_SOCKET']='tcp:127.0.0.1:'+port
 if not env.get('ANTHARES_MEMU_ADB_SERIAL'):
  env['ANTHARES_MEMU_ADB_SERIAL']='127.0.0.1:21543'
 if not env.get('ANTHARES_MEMU_KWAI_AUTHENTICATED'):
  env['ANTHARES_MEMU_KWAI_AUTHENTICATED']='false'
 if job.get('media_sha256') and job.get('media_hash_kind')!='dispatch_identity':env['KWAI_MEDIA_SHA256']=str(job['media_sha256']).lower()
 old=job.get('historical_resolution_evidence')
 if isinstance(old,dict) and old.get('kind')=='kwai_historical_verified_public_absent_v1':
  if old.get('job_id')!=job['id'] or old.get('attested_device')!='DESKTOP-FTDK0HP' or old.get('device_signature_verified') is not True:
   raise RuntimeError('KWAI_HISTORICAL_LEASE_PROOF_INVALID')
  env['KWAI_HISTORICAL_REQUEUE_PROOF_JSON']=json.dumps(old,separators=(',',':'))
 callback=[PYTHON,str(pathlib.Path(__file__).resolve()),'queue-op']
 env['ANTHARES_QUEUE_STARTED_COMMAND_JSON']=json.dumps(callback+['started'])
 env['ANTHARES_QUEUE_COMPLETE_COMMAND_JSON']=json.dumps(callback+['complete'])
 return env
def pubstate(jobid):
 p=PUBSTATE/(re.sub(r'[^A-Za-z0-9._-]+','_',jobid)[-100:]+'.json')
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return {}
def evidence(jobid):
 # Accept only new identity+media-bound proofs; legacy links stay quarantined.
 # A visible profile thumbnail is not evidence of a successfully uploaded post.
 folder=ROOT/'.state'/'kwai-memu-evidence'/re.sub(r'[^A-Za-z0-9._-]+','_',jobid)[-100:]
 proof_file=folder/'public-link-proof.json'
 if not proof_file.is_file():raise RuntimeError('public-link-proof-missing')
 proof=json.loads(proof_file.read_text(encoding='utf-8'))
 if proof.get('kind')=='kwai_public_profile_source_frame_proof_v1':
  native=pubstate(jobid)
  url=str(proof.get('public_url') or '')
  media=proof.get('media_match') or {}
  inliers=media.get('source_best_inliers') or []
  photo=str(proof.get('photo_id') or '')
  legacy=proof.get('placeholder_caption_legacy_recovery') is True
  legacy_ids={
    'kwai-cortes-fOmihuHUT1M-g1-fOmihuHUT1M-461-503',
    'kwai-cortes-fOmihuHUT1M-g1-fOmihuHUT1M-503-543'}
  expected=f'https://www.kwai.com/@{EXPECTED_ACCOUNT}/video/{photo}'
  # Placeholder captions are accepted exclusively for these two published
  # and independently source-matched posts created before the repair.
  if legacy and (jobid not in legacy_ids or proof.get('actual_public_caption')!='...'):
   raise RuntimeError('placeholder_caption_not_allowed_for_new_publication')
  if not legacy and proof.get('title_match') is not True:
   raise RuntimeError('public_caption_does_not_match_job')
  if (proof.get('ok') is not True
      or proof.get('verified_publication_job_id')!=jobid
      or proof.get('expected_account')!=EXPECTED_ACCOUNT
      or proof.get('actual_author_handle')!=EXPECTED_ACCOUNT
      or proof.get('caption')!=native.get('caption')
      or native.get('state')!='verified'
      or native.get('publication_attempted') is not True
      or not re.fullmatch(r'[0-9a-f]{64}',str(native.get('media_sha256') or ''))
      or proof.get('media_sha256')!=native.get('media_sha256')
      or not re.fullmatch(r'[0-9]{16,21}',photo)
      or url!=expected
      or not isinstance(inliers,list)
      or sum(isinstance(v,int) and v>=240 for v in inliers)<4
      or int(media.get('qualifying_distinct_frames') or 0)<4
      or abs(int(proof.get('public_post_timestamp_ms') or 0)
               -int(native.get('publication_attempted_at') or 0)*1000)>8*60*1000):
   raise RuntimeError('kwai_source_matched_public_media_proof_invalid')
  return {'remote_id':url,'confirmation_evidence':{
   'kind':'kwai_public_profile_source_frame_proof_v1',**proof}}
 if proof.get('schema')=='kwai-public-media-proof-v2':
  from kwai_direct_share_proof import validate_job_proof
  return validate_job_proof(jobid,proof,pubstate(jobid))
 url=str(proof.get('public_url') or '')
 native=pubstate(jobid)
 cross=proof.get('cross_device_proof') or {}
 if (proof.get('kind')!='kwai_independent_cross_device_media_bound_v1'
     or proof.get('verified_publication_job_id')!=jobid
     or proof.get('caption')!=native.get('caption')
     or not native.get('media_sha256')
     or proof.get('media_sha256')!=native.get('media_sha256')
     or cross.get('ok') is not True
     or cross.get('public_url')!=proof.get('public_url')
     or cross.get('title_match') is not True
     or cross.get('expected_account')!=EXPECTED_ACCOUNT):
  raise RuntimeError('kwai_cross_device_media_bound_evidence_required')
 if proof.get('ok') is not True or proof.get('expected_account')!=EXPECTED_ACCOUNT or not re.fullmatch(r'https://(?:k\.kwai\.com/p/[A-Za-z0-9_-]+|www\.kwai\.com/@[A-Za-z0-9_.-]+/photo/[0-9]+)',url):
  raise RuntimeError('public-link-proof-invalid')
 return {'remote_id':url,'confirmation_evidence':{'kind':'kwai_verified_public_link',**proof}}
def callback(op):
 jid=os.environ['KWAI_QUEUE_JOB_ID']; gen=int(os.environ['KWAI_LEASE_GENERATION'])
 if op=='started':qpost('started',{'id':jid,'lease_generation':gen});return 0
 if op=='complete':
  st=pubstate(jid)
  if st.get('state')!='verified':raise RuntimeError('profile-not-verified')
  qpost('complete',{'id':jid,'lease_generation':gen,'confirmed':True,**evidence(jid)});return 0
 raise RuntimeError('bad-callback')
def wp_notify(job,status,remote_id='',error=''):
 """Update authoritative CORTES WordPress record after queue publication proof."""
 url=str(job.get('cortes_callback_url') or '')
 token=str(job.get('cortes_callback_token') or '')
 if not url or not token or '/cortes/clip-network-callback' not in url:
  raise RuntimeError('cortes-callback-contract-missing')
 b={'video_id':str(job.get('cortes_video_id') or job.get('source_id') or ''),
    'clip_id':str(job.get('cortes_clip_id') or job.get('segment_id') or ''),
    'attachment_id':int(job.get('cortes_attachment_id') or 0),
    'network':'kwai','account_id':str(job.get('cortes_account_id') or 'primary'),'status':status,'remote_id':remote_id,'error':error[:400],
    'token':token}
 raw=compact(b).encode('utf-8')
 req=urllib.request.Request(url,data=raw,method='POST',headers={
  'Content-Type':'application/json','Accept':'application/json',
  'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36'})
 with urllib.request.urlopen(req,timeout=30) as response:
  data=json.load(response)
 if not isinstance(data,dict) or not data.get('ok'):
  raise RuntimeError('cortes-callback-not-confirmed')
 log('CORTES_WP_CALLBACK_OK '+str(job.get('id'))+' status='+status)

def pending_callbacks():
 try:
  d=json.loads(WP_PENDING.read_text(encoding='utf-8'))
  return d if isinstance(d,dict) else {}
 except FileNotFoundError:return {}

def save_callbacks(rows):
 WP_PENDING.parent.mkdir(parents=True,exist_ok=True)
 temp=WP_PENDING.with_suffix('.tmp')
 temp.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
 temp.replace(WP_PENDING)

def notify_completed(job,remote_id):
 # Persist retry context before calling WordPress; enqueue/central COMPLETE is
 # not proof that the authoritative source record was updated.
 rows=pending_callbacks(); rows[str(job['id'])]={'job':job,'remote_id':remote_id};save_callbacks(rows)
 try:wp_notify(job,'completed',remote_id)
 except Exception as e:
  log('CORTES_WP_CALLBACK_PENDING '+str(job['id'])+' '+type(e).__name__)
  return False
 rows=pending_callbacks();rows.pop(str(job['id']),None);save_callbacks(rows)
 return True

def repair_wp_callbacks():
 for row in list(pending_callbacks().values()):
  notify_completed(row['job'],row['remote_id'])


def mark_ack(jid,state='completed_acknowledged'):
 if state not in ('completed_acknowledged','cancelled_acknowledged'):
  raise ValueError('kwai_terminal_ack_invalid_state')
 try:d=json.loads(ACK.read_text(encoding='utf-8'))
 except Exception:d={}
 row=d.setdefault(jid,{});row['state']=state;row['acknowledged_at']=int(time.time());ACK.parent.mkdir(parents=True,exist_ok=True);ACK.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def preserve_pending_callback_job(job):
 """Retain only origin-callback fields for completion after delayed public proof."""
 jid=str(job['id'])
 try:rows=json.loads(ACK.read_text(encoding='utf-8'))
 except (OSError,ValueError):rows={}
 if not isinstance(rows,dict):rows={}
 row=rows.setdefault(jid,{})
 if row.get('state')!='published_pending_ack':return
 keys=('id','source_id','segment_id','cortes_video_id','cortes_clip_id',
       'cortes_attachment_id','cortes_account_id','account_id',
       'cortes_callback_url','cortes_callback_token')
 row['wp_callback_job']={k:job[k] for k in keys if k in job}
 tmp=ACK.with_suffix('.tmp')
 tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 tmp.replace(ACK)

def complete_origin_callback(jid,row,proof):
 job=row.get('wp_callback_job')
 if isinstance(job,dict) and job.get('id')==jid:
  notify_completed(job,proof['remote_id'])
 else:
  log('KWAI_CONFIRMED_ORIGIN_CALLBACK_CONTEXT_MISSING '+jid)

def terminal_ack_decision(jid,local,remote):
 """Accept only an authenticated Neon terminal receipt for this account/lease."""
 if not isinstance(local,dict) or local.get('state') not in ('published_pending_ack','quarantined_uncertain'):
  return None
 if not isinstance(remote,dict) or remote.get('ok') is not True:
  return None
 try:local_gen=int(local.get('lease_generation') or 0);remote_gen=int(remote.get('lease_generation') or 0)
 except (ValueError,TypeError):return None
 if local_gen<1 or local_gen!=remote_gen or remote.get('id')!=jid or remote.get('target_key')!='kwai:'+EXPECTED_ACCOUNT:
  return None
 state=remote.get('terminal')
 if state=='confirmed':return 'completed_acknowledged'
 if state=='cancelled':return 'cancelled_acknowledged'
 return None


def repair_pending():
 try:d=json.loads(ACK.read_text(encoding='utf-8'))
 except Exception:return
 for jid,row in list(d.items()):
  if not isinstance(row,dict) or row.get('state') not in ('published_pending_ack','quarantined_uncertain'):continue
  # Neon is authoritative. This ACK path only reads server state and updates
  # the existing local receipt; it sends neither video nor SQL mutations.
  try:
   from cortes_neon_queue_client import call
   receipt=call('terminal',{'id':jid,'lease_generation':int(row.get('lease_generation') or 0)})
   decision=terminal_ack_decision(jid,row,receipt)
   if decision:
    mark_ack(jid,decision)
    log('KWAI_LOCAL_ACK_TERMINAL_READ_VERIFIED '+jid+' state='+decision+' no_new_post=1')
    continue
  except Exception as exc:
   log('KWAI_LOCAL_ACK_TERMINAL_READ_UNAVAILABLE '+jid+' error='+type(exc).__name__+' no_mutation=1')
  st=pubstate(jid)
  if st.get('state')!='verified':continue
  proofdir=ROOT/'.state'/'kwai-memu-evidence'/re.sub(r'[^A-Za-z0-9._-]+','_',jid)[-100:]
  if not (proofdir/'public-link-proof.json').is_file():
   stamp=proofdir/'proof-recovery-last-attempt.txt'
   now=int(time.time())
   try:prior=int(stamp.read_text(encoding='utf-8'))
   except (OSError,ValueError):prior=0
   if now-prior>=65:
    proofdir.mkdir(parents=True,exist_ok=True)
    stamp.write_text(str(now),encoding='utf-8')
    env=os.environ.copy()
    env['ANTHARES_PHYSICAL_ADB_PORT']=physical_adb_port()
    env['ANTHARES_ADB']=ADB
    helper=ROOT/'tools'/'kwai_physical_public_proof.py'
    log('KWAI_PROOF_RECOVERY_START '+jid)
    try:
     r=subprocess.run([PYTHON,str(helper),jid],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=220,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
     last=(r.stdout or '').splitlines()[-1][:150] if (r.stdout or '').splitlines() else 'no_stdout'
     pending=('KWAI_PUBLIC_PROFILE_INDEX_PENDING_RETRYABLE' in last or
              'KWAI_PUBLIC_MEDIA_MATCH_PENDING_RETRYABLE' in last or
              'KWAI_PUBLIC_PROFILE_POST_NOT_YET_INDEXED' in last or
              'KWAI_CAPTIONLESS_UNIQUE_MEDIA_PROOF_REQUIRED:0' in last)
     state='OK' if r.returncode==0 else ('PUBLIC_INDEX_PENDING retryable=1' if pending else 'FAILED priority=P0')
     log('KWAI_PROOF_RECOVERY_'+state+' '+jid+' '+last)
    except (OSError,subprocess.TimeoutExpired) as exc:log('KWAI_PROOF_RECOVERY_FAILED priority=P0 '+type(exc).__name__+' '+jid)
   if not (proofdir/'public-link-proof.json').is_file():
    age=now-int(row.get('published_at') or now)
    if row.get('state')=='published_pending_ack' and age>=900 and int(row.get('lease_generation') or 0)>0:
     try:
      result=qpost('fail',{'id':jid,'lease_generation':int(row['lease_generation']),'error_class':'uncertain','error_message':'independent_public_proof_pending','published_possible':True})
      if (result.get('job') or {}).get('status')!='uncertain':raise RuntimeError('central_uncertain_not_confirmed')
      current=json.loads(ACK.read_text(encoding='utf-8'))
      item=current.get(jid) or {}
      if item.get('state')!='published_pending_ack' or int(item.get('lease_generation') or 0)!=int(row['lease_generation']):raise RuntimeError('ack_concurrent_change')
      item['state']='quarantined_uncertain';item['quarantined_at']=now
      tmp=ACK.with_suffix('.tmp')
      tmp.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
      tmp.replace(ACK)
      log('KWAI_UNCERTAIN_QUARANTINED_QUEUE_CONTINUES '+jid)
     except Exception as exc:log('QUEUE_FAIL_CALLBACK_ERROR '+jid+' '+type(exc).__name__)
    continue
  gen=int(row.get('lease_generation') or 0)
  try:
   proof=evidence(jid)
   if gen and row.get('state')=='published_pending_ack':qpost('complete',{'id':jid,'lease_generation':gen,'confirmed':True,**proof})
   else:raise RuntimeError('generation-missing')
   mark_ack(jid)
   complete_origin_callback(jid,row,proof)
   log('ACK_REPAIRED_COMPLETE '+jid);continue
  except Exception as e:log('ACK_COMPLETE_RETRY '+jid+' '+str(e)[-200:])
  try:
   proof=evidence(jid)
   qpost('reconcile',{'id':jid,'confirmed':True,**proof})
   mark_ack(jid)
   complete_origin_callback(jid,row,proof)
   log('ACK_REPAIRED_RECONCILE '+jid)
  except Exception as e:log('ACK_RECONCILE_PENDING '+jid+' '+str(e)[-200:])
def process(job,serial):
 import datetime
 jid=str(job['id']);gen=int(job['lease_generation']);source_id=jid;env=jobenv(job,serial);log(f'JOB_START {jid} gen={gen}')
 p=subprocess.run([PYTHON,str(WORKER)],env=env,cwd=str(ROOT),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=1200,check=False)
 if p.stdout:
  for line in p.stdout.splitlines()[-80:]:log('WORKER '+line)
 if p.returncode==0:
  log('JOB_OK '+jid)
  notify_completed(job,evidence(jid)['remote_id'])
  record_published(jid,datetime.datetime.now().astimezone())
  return
 if p.returncode==91:
  try:
   qpost('complete',{'id':jid,'lease_generation':gen,'confirmed':True,**evidence(jid)})
   mark_ack(jid)
   notify_completed(job,evidence(jid)['remote_id'])
   record_published(jid,datetime.datetime.now().astimezone())
   log('JOB_ACK_REPAIRED '+jid);return
  except Exception as e:
   preserve_pending_callback_job(job)
   log('JOB_ACK_PENDING '+jid+' '+str(e)[-200:])
   record_cut_attempt(source_id,scheduled_at=None,result='failed')
   return
  return
 native_state=pubstate(jid)
 possible=(p.returncode==90 or 'UNCERTAIN' in (p.stdout or '')
           or bool(native_state.get('publication_attempted'))
           or native_state.get('state') in ('publication_attempted','uncertain'))
 try:qpost('fail',{'id':jid,'lease_generation':gen,'error_class':'uncertain' if possible else 'physical_android','error_message':(p.stdout or '')[-450:],'published_possible':possible})
 except Exception as e:log('QUEUE_FAIL_CALLBACK_ERROR '+jid+' '+str(e)[-200:])
 record_cut_attempt(source_id,scheduled_at=None,result='failed')
 log(f'JOB_FAILED {jid} rc={p.returncode} possible={possible}')
 if not possible and p.returncode in (75,81):
  stage_timeout='KWAI_UP_STATE=FAILED ERROR=timeout' in (p.stdout or '')
  arm_preflight_backoff(p.returncode,precommit_timeout=stage_timeout)
def memu_identity_proven():
 """Read-only Kwai account check. Never infer login from app installation."""
 env=os.environ.copy()
 serial=env.get('ANTHARES_MEMU_ADB_SERIAL','127.0.0.1:21543')
 if not ensure_memu_transport(ADB,serial):return False
 env.update({'KWAI_UP_ADB_SERIAL':serial,'KWAI_UP_PACKAGE':'com.kwai.video',
             'KWAI_UP_EXPECTED_ACCOUNT':EXPECTED_ACCOUNT,'ADB_VENDOR_KEYS':ADB_KEYS})
 env['PATH']=str(pathlib.Path(ADB).parent)+os.pathsep+env.get('PATH','')
 script=ROOT/'kwai-up'/'kwai_up_safe.py'
 if not script.is_file():return False
 for attempt in (1,2):
  try:
   p=subprocess.run([PYTHON,str(script),'auth'],env=env,stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,text=True,timeout=95,check=False)
   ok=p.returncode==0 and 'KWAI_UP_STATE=AUTHENTICATED_IDENTITY' in (p.stdout or '') and EXPECTED_ACCOUNT in (p.stdout or '').lower()
   reason=re.search(r'KWAI_UP_STATE=FAILED_SAFE REASON=([A-Za-z0-9_-]+)',p.stdout or '')
   log('MEMU_AUTH_'+('VERIFIED' if ok else 'NOT_VERIFIED')+' attempt='+str(attempt)+' rc='+str(p.returncode)+' reason='+(reason.group(1) if reason else 'none'))
   if ok:return True
  except Exception as e:
   log('MEMU_AUTH_PROBE_ERROR '+type(e).__name__+' attempt='+str(attempt))
  if attempt==1:time.sleep(3)
 return False


_LAST_UNPROVEN_SWEEP_AT=0

def sweep_unproven():
 """Fail-closed authenticated profile reconciling, never requeues an old job."""
 global _LAST_UNPROVEN_SWEEP_AT
 now=time.time()
 if now-_LAST_UNPROVEN_SWEEP_AT<600:return
 _LAST_UNPROVEN_SWEEP_AT=now
 if not PHYSICAL_DEVICE_EXCLUSIVE:return
 script=ROOT/'tools'/'kwai_unproven_reconcile_policy.py'
 if not script.is_file():
  log('KWAI_UNPROVEN_POLICY_HELPER_MISSING no_mutation=1');return
 try:
  from cortes_neon_queue_client import call
  # Reconciled media must also update its original WordPress CORTES record.
  # Retry only that idempotent server-side callback; never repeat the post.
  # Tokens remain inside Neon, absent from arguments and local logs.
  try:
   wp=call('unproven',{'mode':'wp-sync'})
   if not wp.get('ok'):
    log('KWAI_RECONCILED_WP_SYNC_PENDING reason='+str(wp.get('error','unknown'))[:65])
   elif int(wp.get('attempted') or 0):
    log('KWAI_RECONCILED_WP_SYNC attempted='+str(wp.get('attempted'))+
        ' synced='+str(wp.get('synced'))+' pending='+str(wp.get('pending')))
  except Exception as e:
   log('KWAI_RECONCILED_WP_SYNC_RETRY_LATER '+type(e).__name__)
  data=call('unproven',{'mode':'list'})
  if not data.get('ok'):
   log('KWAI_UNPROVEN_POLICY_SERVER_UNAVAILABLE '+str(data.get('error','unknown'))[:85]);return
  jobs=data.get('jobs') or []
  if not jobs:return
 except Exception as e:
  log('KWAI_UNPROVEN_POLICY_CHECK_ERROR '+type(e).__name__);return
 if not acquire_physical_device_lock(EXPECTED_ACCOUNT):
  _LAST_UNPROVEN_SWEEP_AT=0
  log('KWAI_UNPROVEN_PROOF_DEVICE_BUSY no_mutation=1');return
 try:
  env=os.environ.copy()
  env['KWAI_EXPECTED_ACCOUNT']=EXPECTED_ACCOUNT
  env['ANTHARES_ADB']=ADB
  env['ANTHARES_PHYSICAL_ADB_PORT']=physical_adb_port()
  env['ANTHARES_PHYSICAL_ADB_SERIAL']=env.get('ANTHARES_PHYSICAL_ADB_SERIAL','993fce720408')
  p=subprocess.run([PYTHON,str(script)],env=env,cwd=str(ROOT),
        capture_output=True,text=True,timeout=120,check=False,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  for line in (p.stdout or '').splitlines()[-12:]:log('KWAI_UNPROVEN_PROOF '+line[:240])
  log('KWAI_UNPROVEN_SWEEP_RESULT rc='+str(p.returncode)+' total='+str(len(jobs)))
 except subprocess.TimeoutExpired:
  log('KWAI_UNPROVEN_SWEEP_TIMEOUT no_mutation_assumed=0 reconcile_before_retry=1')
 except Exception as e:
  log('KWAI_UNPROVEN_SWEEP_ERROR '+type(e).__name__)
 finally:
  release_physical_device_lock(EXPECTED_ACCOUNT)

def once():
 global LAST_QUEUE_EMPTY,LAST_NETWORK_BAD
 # Maintenance is an absolute fence: prohibit link recovery, ACK callbacks,
 # Android UI, leases and new publications while an incident is active.
 if MAINTENANCE.exists():
  log('QUEUE_PAUSED_MAINTENANCE no_lease=1 no_repair=1')
  return 0
 repair_pending(); repair_wp_callbacks()
 sweep_unproven()
 # Complete any already-posted video before leasing the next job.
 # Public profile metadata may lag publication by several minutes.
 try:
  with ACK.open('r',encoding='utf-8') as fd:acks=json.load(fd)
 except (OSError,ValueError):acks={}
 pending=[jid for jid,row in acks.items() if isinstance(row,dict) and row.get('state')=='published_pending_ack']
 if pending:
  log('KWAI_POSTED_PENDING_CONFIRMATION no_new_lease=1 count='+str(len(pending)))
  return 0
 if owner_cap_reached():return 0
 if retry_gate_active():return 0
 healthy,serial=preflight(); heartbeat(healthy,serial,'' if healthy else 'android-preflight-failed')
 if healthy and serial:
  if not network_ready(serial):
   if not LAST_NETWORK_BAD:log('KWAI_ANDROID_DNS_PREFLIGHT_BLOCKED no_lease=1 priority=P0')
   LAST_NETWORK_BAD=True
   return 75
  if LAST_NETWORK_BAD:log('KWAI_ANDROID_DNS_PREFLIGHT_RECOVERED')
  LAST_NETWORK_BAD=False
 if not healthy:
  # Only consume CORTES work when a tested, authenticated MEmu standby is
  # genuinely available. Its readiness is verified again inside the worker.
  env=os.environ.copy()
  env.setdefault('ANTHARES_ADB',ADB)
  env.setdefault('ANTHARES_MEMU_ADB_SERIAL','127.0.0.1:21543')
  if memu_identity_proven():
   os.environ['ANTHARES_MEMU_KWAI_AUTHENTICATED']='true'
   env['ANTHARES_MEMU_KWAI_AUTHENTICATED']='true'
  try:
   probe=subprocess.run([PYTHON,str(ROOT/'tools'/'android_device_adapters.py')],env=env,capture_output=True,text=True,timeout=35)
   devices=json.loads(probe.stdout) if probe.returncode==0 else {}
   fallback=devices.get('memu_android') or {}
   memu_ok=all(fallback.get(k) is True for k in ('healthy','ready','authenticated'))
  except Exception as e:
   memu_ok=False;log('MEMU_STANDBY_PROBE_ERROR '+str(e)[-200:])
  if not memu_ok:
   log('PREFLIGHT_FAILED no authenticated MEmu fallback available')
   return 75
  log('FAILOVER_TO_VERIFIED_MEMU_PENDING_LEASE')
 if MAINTENANCE.exists():
  log('QUEUE_PAUSED_MAINTENANCE_BEFORE_LEASE no_lease=1')
  return 0
 # Distribui publicações uniformemente entre o primeiro envio e 23h,
 # recalculando intervalos conforme os cortes restantes (máx 100/conta/dia).
 import datetime
 try:
  from cortes_neon_queue_client import call
  now=datetime.datetime.now().astimezone()
  deadline=now.replace(hour=23,minute=0,second=0,microsecond=0)
  available_seconds=max(0,(deadline-now).total_seconds())
  if now>=deadline:
   log('PUBLICATION_WINDOW_CLOSED end=23:00 no_lease=1')
   return 0
  try:
   stats=call('stats',{'target_key':'kwai:'+EXPECTED_ACCOUNT})
  except Exception as stats_err:
   log('PUBLICATION_STATS_UNAVAILABLE exception='+type(stats_err).__name__+' no_lease=1')
   return 0
  if not stats.get('ok') or stats.get('pacing_version')!='kwai-public-post-proportional-06to23-v3':
   log('PUBLICATION_PACING_VERSION_REQUIRED account='+EXPECTED_ACCOUNT+' no_lease=1')
   return 0
  pending=int(stats.get('pending',-1))
  if pending<0:raise RuntimeError('queue_pending_invalid')
  if pending==0:
   if not LAST_QUEUE_EMPTY:log('PUBLICATION_QUEUE_DRAINED stats=verified next_poll_seconds='+str(EMPTY_POLL))
   LAST_QUEUE_EMPTY=True
   return 0
  if LAST_QUEUE_EMPTY:log('PUBLICATION_QUEUE_REPLENISHED pending='+str(pending))
  LAST_QUEUE_EMPTY=False
  today=now.date().isoformat()
  posted_today=int(stats.get('confirmed_today',-1))
  cap=max(1,min(100,int(os.getenv('CORTES_KWAI_DAILY_POST_LIMIT','100'))))
  if posted_today>=cap:
   log('PUBLICATION_DAILY_CAP_REACHED posted='+str(posted_today)+' cap='+str(cap)+' no_lease=1')
   return 0
  # Recalcula o intervalo uniforme conforme os cortes restantes até 23h.
  interval,day_entry=compute_schedule(posted_today, pending, cap, now,stats)
  remaining=int(day_entry.get('remaining',0))
  log('KWAI_SCHEDULE day='+today+' posted='+str(posted_today)+' remaining='+str(remaining)+
      ' cap='+str(cap)+' interval_seconds='+str(interval))
  # Impede novo corte antes do horário previsto no schedule.
  if day_entry.get('status') not in ('DUE','WAIT'):
   log('PUBLICATION_PACING_BLOCKED status='+str(day_entry.get('status'))+' no_lease=1')
   return 0
  due=next_cut_due(now)
  if due and due>now:
   wait=max(1,int((due-now).total_seconds()))
   log('PUBLICATION_SCHEDULED_WAIT seconds='+str(wait)+' next_at='+due.isoformat()+' pending='+str(pending))
   return 0
  # Última publicação ainda dentro do intervalo mínimo?
  # A single Neon-verified due time controls both accounts. With a refill,
  # the deterministic formula is checked again before any lease is requested.
  if day_entry.get('status') not in ('DUE','WAIT'):
   log('PUBLICATION_PACING_BLOCKED status='+str(day_entry.get('status'))+' no_lease=1')
   return 0
  log('PUBLICATION_DUE pending='+str(pending)+' posted_today='+str(posted_today)+' daily_cap='+str(cap)+
      ' interval_seconds='+str(interval))
 except Exception as exc:
  log('PUBLICATION_PACING_SAFE_RETRY error='+type(exc).__name__+' no_lease=1')
  return 0
 if owner_cap_reached():return 0
 # Exclusividade do Android físico: somente um executor por vez, alternando apps.
 # O lock é mantido durante todo o lease + process para impedir uso concorrente.
 physical_locked=False
 if PHYSICAL_DEVICE_EXCLUSIVE:
  owner=EXPECTED_ACCOUNT
  if not acquire_physical_device_lock(owner):
   log('KWAI_PHYSICAL_DEVICE_BUSY owner='+str(_PHYSICAL_DEVICE_OWNER)+' no_lease=1')
   return 0
  physical_locked=True
 try:
  code,d=signed_post('/job/lease',{'executor':EXECUTOR,'platform':'kwai','ttl_seconds':TTL})
  if code//100!=2 or not d.get('ok'):queue_failure('lease',code,d)
  job=d.get('job')
  if not job:log('QUEUE_EMPTY');return 0
  # Impede nova tentativa do mesmo corte antes do horário previsto.
  source_id=str(job['id'])
  allowed,retry_at=can_attempt_cut(source_id,now)
  if not allowed:
   try:qpost('fail',{'id':job['id'],'lease_generation':int(job['lease_generation']),'error_class':'scheduled_retry','error_message':'cut_before_scheduled_time','published_possible':False})
   except Exception as x:log('QUEUE_FAIL_CALLBACK_ERROR '+str(x))
   log('KWAI_CUT_DEFERRED source='+source_id+' retry_at='+str(retry_at))
   return 0
  record_cut_attempt(source_id,scheduled_at=None,result='leased')
  try:process(job,serial)
  except RuntimeError as e:
   log('JOB_PRESTART_ERROR '+str(e))
   try:qpost('fail',{'id':job['id'],'lease_generation':int(job['lease_generation']),'error_class':'preflight','error_message':str(e),'published_possible':False})
   except Exception as x:log('QUEUE_FAIL_CALLBACK_ERROR '+str(x))
 finally:
  if physical_locked:
   release_physical_device_lock(EXPECTED_ACCOUNT)
 return 0
def lock():
 LOGDIR.mkdir(parents=True,exist_ok=True)
 try:fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());return fd
 except FileExistsError:
  try:
   pid=int(LOCK.read_text().strip());subprocess.run(['tasklist','/FI',f'PID eq {pid}'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=5)
  except Exception:pid=0
  if pid:
   p=subprocess.run(['tasklist','/FI',f'PID eq {pid}'],stdout=subprocess.PIPE,text=True).stdout
   if str(pid) in p:raise RuntimeError('daemon-already-running')
  LOCK.unlink(missing_ok=True);return lock()
def daemon():
 fd=lock()
 log('DAEMON_STARTED pid='+str(os.getpid())+' account='+EXPECTED_ACCOUNT)
 secondary=None
 parent_pid=int(os.getenv('ANTHARES_KWAI_PARENT_DAEMON_PID','0') or '0')
 dual=(EXPECTED_ACCOUNT=='lucasrosalem' and os.getenv('ANTHARES_KWAI_SECONDARY_ENABLED','0')=='1')
 last_secondary_restart=0
 def parent_is_alive():
  if parent_pid<=0:return True
  try:
   result=subprocess.run(['tasklist','/FI','PID eq '+str(parent_pid)],capture_output=True,text=True,timeout=8)
   return result.returncode==0 and str(parent_pid) in (result.stdout or '')
  except Exception:return False
 def launch_secondary():
  childenv=os.environ.copy()
  childenv.update(KWAI_EXPECTED_ACCOUNT='universoanthares',
                  CORTES_QUEUE_TARGET='kwai:universoanthares',
                  ANTHARES_KWAI_SECONDARY_ENABLED='0',
                  ANTHARES_KWAI_PARENT_DAEMON_PID=str(os.getpid()),
                  ANTHARES_KWAI_FORCE_MEMU='0',
                  ANTHARES_KWAI_PHYSICAL_PRIMARY_EXCLUSIVE='1',
                  ANTHARES_PHYSICAL_ADB_PORT='5038')
  return subprocess.Popen([PYTHON,str(pathlib.Path(__file__).resolve()),'daemon'],env=childenv,
                          stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 last_tick=0
 try:
  if dual:
   secondary=launch_secondary()
   last_secondary_restart=time.monotonic()
   log('KWAI_SECONDARY_DAEMON_STARTED pid='+str(secondary.pid))
  while True:
   if not parent_is_alive():
    log('KWAI_SECONDARY_PARENT_EXITED')
    break
   if dual and secondary is not None and secondary.poll() is not None:
    log('KWAI_SECONDARY_DAEMON_EXITED rc='+str(secondary.returncode))
    secondary=None
   if dual and secondary is None and time.monotonic()-last_secondary_restart>=120:
    secondary=launch_secondary()
    last_secondary_restart=time.monotonic()
    log('KWAI_SECONDARY_DAEMON_RESTARTED pid='+str(secondary.pid))
   if time.monotonic()-last_tick>=120:
    log('DAEMON_TICK pid='+str(os.getpid()))
    last_tick=time.monotonic()
   delay=POLL
   try:
    once()
    if LAST_QUEUE_EMPTY:delay=EMPTY_POLL
   except QueueStorageBlocked:
    delay=900
    log('QUEUE_BLOCKED reason=queue_storage_quota_exhausted retry_seconds=900 no_publication_attempted=1')
   except Exception as e:
    log('LOOP_ERROR '+repr(e))
    try:heartbeat(False,'',str(e))
    except Exception:pass
   time.sleep(delay)
 finally:
  if secondary is not None and secondary.poll() is None:
   secondary.terminate()
   try:secondary.wait(timeout=10)
   except subprocess.TimeoutExpired:secondary.kill()
  os.close(fd)
  LOCK.unlink(missing_ok=True)

def single_run():
 fd=lock()
 try:return once()
 finally:os.close(fd);LOCK.unlink(missing_ok=True)
def main():
 if len(sys.argv)>=3 and sys.argv[1]=='queue-op':return callback(sys.argv[2])
 if len(sys.argv)>=2 and sys.argv[1]=='heartbeat-once':
  h,s=preflight();code,d=heartbeat(h,s,'' if h else 'android-preflight-failed');print(compact({'http':code,'response':d,'healthy':h,'serial':s}));return 0 if code//100==2 and d.get('ok') else 1
 if len(sys.argv)>=2 and sys.argv[1]=='once':return single_run()
 if len(sys.argv)>=2 and sys.argv[1]=='daemon':return daemon() or 0
 print('usage: kwai_physical_queue_daemon.py daemon|once|heartbeat-once|queue-op OP');return 2
if __name__=='__main__':raise SystemExit(main())
