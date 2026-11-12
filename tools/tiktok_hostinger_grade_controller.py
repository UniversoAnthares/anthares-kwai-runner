#!/usr/bin/env python3
"""Anthares: one 35-minute TikTok LIVE per Hostinger cron-owned worker."""
import ctypes,datetime,fcntl,json,os,pathlib,re,signal,subprocess,sys,tempfile,time
os.umask(0o077)
R=pathlib.Path('/home/u566597497/.anthares-tiktok-restream')
D=R/'grade';D.mkdir(mode=0o700,exist_ok=True)
SRC=R/'normalized/show-double.ffconcat'
FF='/home/u566597497/bin/ffmpeg-static/ffmpeg'
H=R/'cloud-failover.py'
def epoch():return int(time.time())
def enabled():return read('enabled')=='yes'
def read(p,default=''):
 try:return (D/p).read_text().strip()
 except OSError:return default
def atom(p,s):
 fd,tmp=tempfile.mkstemp(prefix='.grade-save-',dir=str(D))
 try:
  os.fchmod(fd,0o600)
  with os.fdopen(fd,'w') as o:o.write(str(s)+'\n')
  os.replace(tmp,str(D/p))
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def state():
 try:return json.loads(read('state.json'))
 except Exception:return {'count':0,'failures':0,'next_at':0}
def save(s):atom('state.json',json.dumps(s,sort_keys=True))
def rec(kind,**v):
 record={'utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),'event':kind}
 record.update(v)
 with (D/'events.jsonl').open('a') as o:o.write(json.dumps(record,sort_keys=True)+'\n')
 print('GRADE_EVENT='+kind,flush=True)
def cmd(action,owner=''):
 a=['python3',str(H),action]+([str(owner)] if owner else [])
 p=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=43)
 if p.returncode:raise RuntimeError('host_'+action+':'+p.stdout[-100:])
 return p.stdout
def hostmode():return (R/'enabled').read_text().strip()
def belongs(pid,needle):
 try:return needle.encode() in pathlib.Path('/proc/{}/cmdline'.format(int(pid))).read_bytes()
 except (OSError,ValueError):return False
def owner():return read('owner')
def other_claim():
 lease=R/'cloud-primary-lease'
 if not lease.exists():return False
 v=lease.read_text().split()
 return len(v)!=2 or v[0]!=owner()
def running():return bool(read('worker.pid') and belongs(read('worker.pid'),str(pathlib.Path(__file__).resolve())))
def guard(name):
 f=(D/name).open('a')
 try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);return f
 except (IOError,OSError):f.close();return None
def clear_orphan():
 pid=read('ffmpeg.pid')
 if not pid:return True
 if belongs(pid,str(D/'live.progress')):
  rec('orphan_found')
  try:os.kill(int(pid),signal.SIGTERM)
  except OSError:pass
  for _ in range(25):
   if not belongs(pid,str(D/'live.progress')):break
   time.sleep(.2)
  if belongs(pid,str(D/'live.progress')):rec('orphan_still_running');return False
 atom('ffmpeg.pid','')
 return True
def dest():
 if not SRC.is_file() or not (R/'normalized/full-validation.json').is_file():raise RuntimeError('source_missing')
 if json.loads((R/'normalized/full-validation.json').read_text()).get('good') is not True:raise RuntimeError('source_unvalidated')
 u=(R/'rtmp-destination').read_text().strip()
 if not re.match(r'^rtmps?://live\.restream\.io/live/[^\s]+$',u):raise RuntimeError('invalid_rtmp')
 return u
def tick():
 lock=guard('tick.lock')
 if not lock:return
 try:
  if not enabled():print('GRADE_TICK=inactive',flush=True);return
  if running():print('GRADE_TICK=healthy',flush=True);return
  if other_claim():rec('different_stream_owner');return
  if hostmode()=='false':atom('enabled','no');rec('operator_disabled');return
  s=state()
  if s.get('failures',0)>=3:atom('enabled','no');rec('circuit_open');return
  if epoch()<s.get('next_at',0):print('GRADE_TICK=waiting',flush=True);return
  if not clear_orphan():return
  with (D/'worker.log').open('a') as o:
   w=subprocess.Popen(['python3','-u',str(pathlib.Path(__file__).resolve()),'worker'],stdin=subprocess.DEVNULL,stdout=o,stderr=subprocess.STDOUT,close_fds=True,start_new_session=True)
  atom('worker.pid',str(w.pid))
  rec('worker_spawned',pid=w.pid)
 finally:lock.close()
def pdeath():
 ctypes.CDLL(None).prctl(1,signal.SIGTERM,0,0,0);os.setsid()
def worker():
 lk=guard('worker.lock')
 if not lk:return
 child=None;claimed=False;failure=None;who=owner();number=0
 try:
  if not enabled():raise RuntimeError('grade_off')
  url=dest()
  if hostmode()=='true':
   if 'CLOUD_CLAIM=PASS' not in cmd('claim',who):raise RuntimeError('claim_failed')
   claimed=True
  elif hostmode()=='cloud':
   if other_claim():raise RuntimeError('owner_conflict')
   cmd('heartbeat',who);claimed=True
  else:raise RuntimeError('operator_disarmed')
  period=float(json.loads((R/'normalized/build-state.json').read_text())['total_duration'])
  origin=int((R/'program-origin-epoch').read_text().strip())
  position=int((time.time()-origin)%period)
  length=int(read('duration','2100'))
  if not 120<=length<=2400:raise RuntimeError('duration_out_of_range')
  progress=D/'live.progress';progress.write_text('');progress.chmod(0o600)
  errorfile=D/'live.stderr'
  args=[FF,'-y','-nostdin','-hide_banner','-loglevel','error','-fflags','+genpts',
        '-re','-ss',str(position),'-f','concat','-safe','0','-i',str(SRC),'-t',str(length),
        '-c:v','copy','-c:a','copy','-avoid_negative_ts','make_zero','-f','flv',
        '-progress',str(progress),url]
  with errorfile.open('w') as o:
   child=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=o,close_fds=True,preexec_fn=pdeath)
  atom('ffmpeg.pid',child.pid)
  s=state();number=s.get('count',0)+1;s.update(count=number,last_start=epoch(),next_at=0);save(s)
  rec('live_started',number=number,pid=child.pid,position=position,length=length)
  start=time.monotonic();last=start;old_size=-1;renew=0
  while child.poll() is None:
   if not enabled():raise RuntimeError('grade_disabled')
   if time.monotonic()-start>length+45:raise RuntimeError('session_timeout')
   if time.monotonic()>=renew:cmd('heartbeat',who);renew=time.monotonic()+31
   if progress.exists():
    sz=progress.stat().st_size
    if sz>old_size:old_size=sz;last=time.monotonic()
   if time.monotonic()-last>110:raise RuntimeError('no_progress')
   time.sleep(4)
  if child.returncode:raise RuntimeError('ffmpeg_failed_'+str(child.returncode))
  if 'progress=end' not in progress.read_text():raise RuntimeError('end_missing')
  if errorfile.stat().st_size:raise RuntimeError('ffmpeg_errors')
  gap=int(read('gap_seconds','80'))
  if not 15<=gap<=180:raise RuntimeError('gap_invalid')
  s=state();s.update(failures=0,last_end=epoch(),next_at=epoch()+gap);save(s)
  rec('live_completed',number=number,seconds=round(time.monotonic()-start,1),next_at=s['next_at'])
 except Exception as e:
  failure=str(e)[:120]
  s=state();s.update(failures=s.get('failures',0)+1,next_at=epoch()+90);save(s)
  rec('live_failed',number=number,reason=failure,failures=s['failures'])
 finally:
  if child is not None and child.poll() is None:
   child.terminate()
   try:child.wait(timeout=8)
   except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
  if child is not None and read('ffmpeg.pid')==str(child.pid):atom('ffmpeg.pid','')
  if claimed:
   if not enabled() or state().get('failures',0)>=3:
    atom('enabled','no')
    try:cmd('release',who);rec('host_restored')
    except Exception:rec('host_recovery_waiting_lease')
   else:
    try:cmd('heartbeat',who)
    except Exception:rec('final_heartbeat_failed')
  lk.close()
 if failure:raise RuntimeError(failure)
def status():
 print('GRADE_ENABLED='+str(int(enabled())))
 print('GRADE_RUNNING='+str(int(running())))
 print('GRADE_HOST_MODE='+hostmode())
 s=state()
 for k in ['count','failures','next_at','last_start','last_end']:print('GRADE_'+k.upper()+'='+str(s.get(k,'')))
 print('GRADE_GAP='+read('gap_seconds','80'))
def enable():
 if enabled():tick();return
 if hostmode()!='true' or (R/'cloud-primary-lease').exists():raise RuntimeError('another_stream_owns_rtmp')
 dest()
 atom('owner',epoch());atom('duration',2100)
 if not read('gap_seconds'):atom('gap_seconds',80)
 save({'count':0,'failures':0,'next_at':0,'activated':epoch()})
 atom('enabled','yes');rec('grade_enabled',length=2100,gap=int(read('gap_seconds')))
 tick()
def disable():
 atom('enabled','no');rec('grade_disabled')
 for _ in range(16):
  if not running():break
  time.sleep(.5)
 if not running():
  clear_orphan()
  if hostmode()=='cloud' and not other_claim():
   try:cmd('release',owner());rec('host_restored')
   except Exception:rec('host_recovery_waiting_lease')
 status()
if __name__=='__main__':
 try:
  op=sys.argv[1] if len(sys.argv)>1 else 'status'
  if op=='tick':tick()
  elif op=='worker':worker()
  elif op=='enable':enable()
  elif op=='disable':disable()
  elif op=='status':status()
  else:raise RuntimeError('unknown_command')
 except Exception as e:print('GRADE_ERROR='+str(e)[:130],flush=True);sys.exit(1)