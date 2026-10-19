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
WORKER=ROOT/'tools'/'kwai_device_failover_worker.py'; ACK=ROOT/'.state'/'android-publish-ack.json'; PUBSTATE=ROOT/'.state'/'kwai-native-cortes'
LOGDIR=ROOT/'.state'; LOG=LOGDIR/'kwai-physical-queue.log'; LOCK=LOGDIR/'kwai-physical-queue.lock'; MAINTENANCE=LOGDIR/'cortes-publisher-maintenance.pause'
TTL=3600; POLL=20
WP_PENDING=LOGDIR/'cortes-wp-callback-pending.json'
_key=None

class QueueStorageBlocked(RuntimeError):
 pass

def queue_failure(op,code,data):
 if code==503 and data.get('error')=='queue_storage_quota_exhausted':
  raise QueueStorageBlocked('queue_storage_quota_exhausted')
 raise RuntimeError(f'queue-{op}:{code}:{data}')

def log(msg):
 LOGDIR.mkdir(parents=True,exist_ok=True); line=time.strftime('%Y-%m-%dT%H:%M:%S')+' '+msg; print(line,flush=True)
 try:
  with LOG.open('a',encoding='utf-8') as f:f.write(line+'\n')
 except OSError:pass

def compact(d):return json.dumps(d,separators=(',',':'),ensure_ascii=False)
def key():
 global _key
 if _key is None:
  _key=serialization.load_pem_private_key(PRIVATE_KEY.read_bytes(),password=None)
 return _key
def signed_post(path,payload,timeout=30):
 if os.getenv('CORTES_QUEUE_BACKEND','cloudflare').strip().lower()=='neon' and path.startswith('/job/'):
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

def adb(*a,timeout=25,check=False):
 env=os.environ.copy(); env['ADB_VENDOR_KEYS']=ADB_KEYS
 return subprocess.run([ADB,*a],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=timeout,check=check,env=env)
def devices():
 p=adb('devices','-l')
 return online_devices(p.stdout) if p.returncode==0 else []
def resolve_serial():
 for d in devices():
  if d.get('model')==MODEL:return d['serial']
 p=adb('mdns','services')
 for ep in re.findall(r'(\d{1,3}(?:\.\d{1,3}){3}:\d+)',p.stdout or ''):
  adb('connect',ep,timeout=20)
 for d in devices():
  if d.get('model')==MODEL:return d['serial']
 raise RuntimeError('physical-device-unavailable')
def preflight():
 try:
  s=resolve_serial(); state=adb('-s',s,'get-state').stdout.strip(); model=adb('-s',s,'shell','getprop','ro.product.model').stdout.strip(); pkg=adb('-s',s,'shell','pm','path','kwai.lite.video').stdout
  native=adb('-s',s,'shell','test','-x','/data/local/tmp/anthares-kwai-native.sh').returncode==0
  touch=adb('-s',s,'shell','test','-x','/data/local/tmp/anthares-hid-tap.sh').returncode==0
  return bool(state=='device' and model==MODEL and 'package:' in pkg and native and touch),s
 except Exception:return False,''
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
 env=os.environ.copy(); env.update({'ADB_VENDOR_KEYS':ADB_KEYS,'ANTHARES_ADB':ADB,'ANTHARES_PHYSICAL_ADB_SERIAL':serial,'KWAI_QUEUE_JOB_ID':str(job['id']),'KWAI_LEASE_OWNER':str(job.get('lease_owner') or ''),'KWAI_LEASE_GENERATION':str(job['lease_generation']),'KWAI_SOURCE_ID':str(job['source_id']),'KWAI_SOURCE_START':str(job['source_start']),'KWAI_SOURCE_END':str(job['source_end']),'KWAI_VIDEO_URL':str(job['video_url']),'KWAI_VIDEO_TITLE':str(job.get('video_title') or ''),'KWAI_EXPECTED_ACCOUNT':account})

 # Mark the primary as transport-ready, but identity verification remains in
 # kwai_up_safe.prepare() before STARTED. Never infer MEmu login readiness.
 env['ANTHARES_PHYSICAL_KWAI_AUTHENTICATED']='true' if serial else 'false'
 if not env.get('ANTHARES_MEMU_ADB_SERIAL'):
  env['ANTHARES_MEMU_ADB_SERIAL']='127.0.0.1:21543'
 if not env.get('ANTHARES_MEMU_KWAI_AUTHENTICATED'):
  env['ANTHARES_MEMU_KWAI_AUTHENTICATED']='false'
 if job.get('media_sha256') and job.get('media_hash_kind')!='dispatch_identity':env['KWAI_MEDIA_SHA256']=str(job['media_sha256']).lower()
 callback=[PYTHON,str(pathlib.Path(__file__).resolve()),'queue-op']
 env['ANTHARES_QUEUE_STARTED_COMMAND_JSON']=json.dumps(callback+['started'])
 env['ANTHARES_QUEUE_COMPLETE_COMMAND_JSON']=json.dumps(callback+['complete'])
 return env
def pubstate(jobid):
 p=PUBSTATE/(re.sub(r'[^A-Za-z0-9._-]+','_',jobid)[-100:]+'.json')
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return {}
def evidence(jobid):
 # Queue COMPLETE requires independently verified, user-openable Kwai URL.
 # Profile thumbnail changes or a click on Publish are not publication proof.
 folder=ROOT/'.state'/'kwai-memu-evidence'/re.sub(r'[^A-Za-z0-9._-]+','_',jobid)[-100:]
 proof_file=folder/'public-link-proof.json'
 if not proof_file.is_file():
  raise RuntimeError('public-link-proof-missing')
 proof=json.loads(proof_file.read_text(encoding='utf-8'))
 url=str(proof.get('public_url') or '')
 if proof.get('ok') is not True or proof.get('expected_account')!=EXPECTED_ACCOUNT or not re.fullmatch(r'https://(?:k\\.kwai\\.com/p/[A-Za-z0-9_-]+|www\\.kwai\\.com/@[A-Za-z0-9_.-]+/photo/[0-9]+)',url):
  raise RuntimeError('public-link-proof-invalid')
 return {'remote_id':url,'confirmation_evidence':proof}
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


def mark_ack(jid):
 try:d=json.loads(ACK.read_text(encoding='utf-8'))
 except Exception:d={}
 row=d.setdefault(jid,{});row['state']='completed_acknowledged';row['acknowledged_at']=int(time.time());ACK.parent.mkdir(parents=True,exist_ok=True);ACK.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def repair_pending():
 try:d=json.loads(ACK.read_text(encoding='utf-8'))
 except Exception:return
 for jid,row in list(d.items()):
  if not isinstance(row,dict) or row.get('state')!='published_pending_ack':continue
  st=pubstate(jid)
  if st.get('state')!='verified':continue
  gen=int(row.get('lease_generation') or 0)
  try:
   if gen:qpost('complete',{'id':jid,'lease_generation':gen,'confirmed':True,**evidence(jid)})
   else:raise RuntimeError('generation-missing')
   mark_ack(jid);log('ACK_REPAIRED_COMPLETE '+jid);continue
  except Exception as e:log('ACK_COMPLETE_RETRY '+jid+' '+str(e)[-200:])
  try:
   qpost('reconcile',{'id':jid,'confirmed':True,**evidence(jid)});mark_ack(jid);log('ACK_REPAIRED_RECONCILE '+jid)
  except Exception as e:log('ACK_RECONCILE_PENDING '+jid+' '+str(e)[-200:])
def process(job,serial):
 jid=str(job['id']);gen=int(job['lease_generation']);env=jobenv(job,serial);log(f'JOB_START {jid} gen={gen}')
 p=subprocess.run([PYTHON,str(WORKER)],env=env,cwd=str(ROOT),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=1200,check=False)
 if p.stdout:
  for line in p.stdout.splitlines()[-80:]:log('WORKER '+line)
 if p.returncode==0:
  log('JOB_OK '+jid)
  notify_completed(job,evidence(jid)['remote_id'])
  return
 if p.returncode==91:
  try:
   qpost('complete',{'id':jid,'lease_generation':gen,'confirmed':True,**evidence(jid)})
   mark_ack(jid)
   notify_completed(job,evidence(jid)['remote_id'])
   log('JOB_ACK_REPAIRED '+jid);return
  except Exception as e:log('JOB_ACK_PENDING '+jid+' '+str(e)[-200:]);return
 possible=p.returncode==90 or 'UNCERTAIN' in (p.stdout or '')
 try:qpost('fail',{'id':jid,'lease_generation':gen,'error_class':'uncertain' if possible else 'physical_android','error_message':(p.stdout or '')[-450:],'published_possible':possible})
 except Exception as e:log('QUEUE_FAIL_CALLBACK_ERROR '+jid+' '+str(e)[-200:])
 log(f'JOB_FAILED {jid} rc={p.returncode} possible={possible}')
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
   log('MEMU_AUTH_'+('VERIFIED' if ok else 'NOT_VERIFIED')+' attempt='+str(attempt)+' rc='+str(p.returncode))
   if ok:return True
  except Exception as e:
   log('MEMU_AUTH_PROBE_ERROR '+type(e).__name__+' attempt='+str(attempt))
  if attempt==1:time.sleep(3)
 return False


def once():
 if MAINTENANCE.exists():
  log('QUEUE_PAUSED_MAINTENANCE no_lease=1')
  return 0
 repair_pending(); repair_wp_callbacks(); healthy,serial=preflight(); heartbeat(healthy,serial,'' if healthy else 'android-preflight-failed')
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
 code,d=signed_post('/job/lease',{'executor':EXECUTOR,'platform':'kwai','ttl_seconds':TTL})
 if code//100!=2 or not d.get('ok'):queue_failure('lease',code,d)
 job=d.get('job')
 if not job:log('QUEUE_EMPTY');return 0
 try:process(job,serial)
 except RuntimeError as e:
  log('JOB_PRESTART_ERROR '+str(e))
  try:qpost('fail',{'id':job['id'],'lease_generation':int(job['lease_generation']),'error_class':'preflight','error_message':str(e),'published_possible':False})
  except Exception as x:log('QUEUE_FAIL_CALLBACK_ERROR '+str(x))
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
 log('DAEMON_STARTED pid='+str(os.getpid()))
 try:
  while True:
   delay=POLL
   try:once()
   except QueueStorageBlocked:
    delay=900
    log('QUEUE_BLOCKED reason=queue_storage_quota_exhausted retry_seconds=900 no_publication_attempted=1')
   except Exception as e:
    log('LOOP_ERROR '+repr(e));
    try:heartbeat(False,'',str(e))
    except Exception:pass
   time.sleep(delay)
 finally:os.close(fd);LOCK.unlink(missing_ok=True)
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
