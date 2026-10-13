from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
MEMU_DIR=Path(r"D:\Program Files\Microvirt\MEmu"); MEMUC=MEMU_DIR/"memuc.exe"; MEMU=MEMU_DIR/"MEmu.exe"; ADB=MEMU_DIR/"adb.exe"
RUNTIME=Path(r"D:\AntharesWork\legacy-pc-runtime"); DOWNLOADS=RUNTIME/"downloads"; INSTALLER=DOWNLOADS/"MEmu-Setup-9.5.7.1.exe"
TARGET_REPO=Path(r"D:\AntharesWork\anthares-clipper"); WORK=Path(r"D:\AntharesWork\kwai-publisher"); LIVE_MEDIA=Path(r"D:\AntharesWork\live-media")
VAULT_ZIP=DOWNLOADS/"kwai-vault.zip"; VAULT_DIR=RUNTIME/"kwai-vault"; VAULT_URL="https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/kwai-package-vault/kwai-vault.zip"
VAULT_SHA256="96650454576a2cf5cc5e63d90011f0b60a03d2702605756f40cc934cd6ae5543"; DAEMON_SHA256="14b31d4bfe50b6b0b3103b08daab693132a9e7926c4eb12dd1ba6f403c088527"; PUBLISHER_SHA256="5257623f994be9b2b12b4fed9dc1996616784004af4a490e41b88fd2f36650b0"; EXPECTED_KWAI_VERSION="13.8.30.646601"; REPORT=RUNTIME/"item1-historical-env-report.json"
def now(): return datetime.now(timezone.utc).isoformat()
def sha256(path):
 h=hashlib.sha256(); f=path.open('rb')
 try:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 finally: f.close()
 return h.hexdigest()
def run(argv,timeout=120,check=False):
 p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,timeout=timeout)
 if check and p.returncode!=0: raise RuntimeError(f"command failed rc={p.returncode}: {argv}\nSTDOUT={p.stdout[-4000:]}\nSTDERR={p.stderr[-4000:]}")
 return p
def memuc(*args,timeout=180,check=False): return run([MEMUC,*args],timeout=timeout,check=check)
def ensure_memu(report):
 DOWNLOADS.mkdir(parents=True,exist_ok=True)
 if not(MEMUC.exists() and MEMU.exists() and ADB.exists()):
  if not INSTALLER.exists(): raise RuntimeError(f"MEmu missing and verified installer absent: {INSTALLER}")
  p=run([INSTALLER,"/S"],timeout=600)
  if p.returncode not in (0,3010): raise RuntimeError(f"MEmu installer failed rc={p.returncode}: {p.stdout[-2000:]} {p.stderr[-2000:]}")
  for _ in range(60):
   if MEMUC.exists() and MEMU.exists() and ADB.exists(): break
   time.sleep(2)
 if not(MEMUC.exists() and MEMU.exists() and ADB.exists()): raise RuntimeError("MEmu runtime incomplete after repair")
 v=memuc("--version",timeout=30); report['memu']={'path':str(MEMU_DIR),'memuc_version_output':(v.stdout+v.stderr).strip(),'present':True}
def vm_indices():
 p=memuc("listvms",timeout=60,check=True); out=p.stdout+'\n'+p.stderr; found=[]
 for line in out.splitlines():
  m=re.match(r"\s*(\d+)\s*[,| ]",line)
  if m: found.append(int(m.group(1)))
 return sorted(set(found))
def vm_prop(index,prop):
 p=memuc("adb","-i",str(index),"-c",f"shell getprop {prop}",timeout=45); lines=(p.stdout+'\n'+p.stderr).strip().splitlines(); return lines[-1].strip() if lines else ''
def ensure_vm3(report):
 indices=vm_indices()
 if 3 not in indices:
  source=None
  for idx in indices:
   try:
    memuc("start","-i",str(idx),timeout=180); time.sleep(3); release=vm_prop(idx,"ro.build.version.release"); abi=vm_prop(idx,"ro.product.cpu.abi")
    if release.startswith('9') and 'x86_64' in abi: source=idx; break
   except Exception: pass
  while 3 not in vm_indices():
   if source is not None: memuc("clone","-i",str(source),timeout=600,check=True)
   else:
    p=memuc("create","90",timeout=900)
    if p.returncode!=0: raise RuntimeError(f"Unable to recreate Android 9 VM: {p.stdout[-3000:]} {p.stderr[-3000:]}")
 memuc("start","-i","3",timeout=180); booted=False
 for _ in range(120):
  p=memuc("adb","-i","3","-c","shell getprop sys.boot_completed",timeout=30)
  if '1' in (p.stdout+p.stderr).split(): booted=True; break
  time.sleep(2)
 if not booted: raise RuntimeError("VM3 did not complete Android boot")
 release=vm_prop(3,"ro.build.version.release"); abi=vm_prop(3,"ro.product.cpu.abi")
 if not release.startswith('9'): raise RuntimeError(f"VM3 Android version mismatch: {release!r}")
 if 'x86_64' not in abi: raise RuntimeError(f"VM3 ABI mismatch: {abi!r}")
 report['vm3']={'exists':True,'android':release,'abi':abi,'adb':True}
def kwai_version():
 p=memuc("adb","-i","3","-c","shell dumpsys package com.kwai.video",timeout=90); text=p.stdout+'\n'+p.stderr; m=re.search(r"versionName=([^\s]+)",text); return m.group(1).strip() if m else ''
def ensure_kwai(report):
 version=kwai_version()
 if version!=EXPECTED_KWAI_VERSION:
  DOWNLOADS.mkdir(parents=True,exist_ok=True)
  if not VAULT_ZIP.exists() or sha256(VAULT_ZIP)!=VAULT_SHA256:
   tmp=VAULT_ZIP.with_suffix('.zip.tmp')
   with urllib.request.urlopen(VAULT_URL,timeout=180) as r, tmp.open('wb') as f: shutil.copyfileobj(r,f)
   if sha256(tmp)!=VAULT_SHA256: tmp.unlink(missing_ok=True); raise RuntimeError('Kwai vault archive SHA-256 mismatch')
   os.replace(tmp,VAULT_ZIP)
  if sha256(VAULT_ZIP)!=VAULT_SHA256: raise RuntimeError('Kwai vault SHA-256 mismatch')
  if VAULT_DIR.exists(): shutil.rmtree(VAULT_DIR)
  VAULT_DIR.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(VAULT_ZIP) as zf: zf.extractall(VAULT_DIR)
  apks=sorted(VAULT_DIR.rglob('*.apk'))
  if len(apks)!=11: raise RuntimeError(f"Expected 11 Kwai APK splits, found {len(apks)}")
  cmd='install-multiple -r '+' '.join(f'\"{p}\"' for p in apks); p=memuc('adb','-i','3','-c',cmd,timeout=900)
  if p.returncode!=0 or 'Success' not in (p.stdout+p.stderr): raise RuntimeError(f"Kwai split install failed: {p.stdout[-5000:]} {p.stderr[-5000:]}")
  version=kwai_version()
 if version!=EXPECTED_KWAI_VERSION: raise RuntimeError(f"Kwai version mismatch after repair: {version!r}")
 report['kwai']={'package':'com.kwai.video','version':version,'vault_sha256':VAULT_SHA256,'splits_expected':11}
def candidate_source():
 for root in [Path(r"C:\Users\Lucas\anthares-clipper"),Path(r"C:\Users\Lucas\AntharesWork\anthares-clipper-cloud")]:
  d=root/'kwai_daily_daemon.py'; p=root/'kwai_memu_publish.py'
  if d.is_file() and p.is_file() and sha256(d)==DAEMON_SHA256 and sha256(p)==PUBLISHER_SHA256: return root
 raise RuntimeError('No preserved source copy with both exact recovered Kwai hashes was found')
def target_exact():
 d=TARGET_REPO/'kwai_daily_daemon.py'; p=TARGET_REPO/'kwai_memu_publish.py'; return d.is_file() and p.is_file() and sha256(d)==DAEMON_SHA256 and sha256(p)==PUBLISHER_SHA256
def ensure_historical_code(report):
 source=candidate_source(); backup=None
 if not target_exact():
  if TARGET_REPO.exists():
   stamp=datetime.now().strftime('%Y%m%d-%H%M%S'); backup=TARGET_REPO.with_name(f"anthares-clipper.pre-historical-{stamp}"); TARGET_REPO.rename(backup)
  shutil.copytree(source,TARGET_REPO,ignore=shutil.ignore_patterns('__pycache__','*.pyc','tmp'))
 if not target_exact(): raise RuntimeError('Historical Kwai code hashes do not match after restoration')
 WORK.mkdir(parents=True,exist_ok=True); LIVE_MEDIA.mkdir(parents=True,exist_ok=True)
 for fn in ('kwai_daily_daemon.py','kwai_memu_publish.py'):
  p=run([sys.executable,'-m','py_compile',str(TARGET_REPO/fn)],timeout=120)
  if p.returncode!=0: raise RuntimeError(f"Python compile failed for {fn}: {p.stderr}")
 report['historical_code']={'source':str(source),'target':str(TARGET_REPO),'backup_created':str(backup) if backup else None,'daemon_sha256':sha256(TARGET_REPO/'kwai_daily_daemon.py'),'publisher_sha256':sha256(TARGET_REPO/'kwai_memu_publish.py'),'python_compile':True,'work_dir':str(WORK),'live_media_dir':str(LIVE_MEDIA)}
def main():
 RUNTIME.mkdir(parents=True,exist_ok=True); report={'started_at':now(),'item':'historical_kwai_environment_1','publication_attempted':False}
 try:
  ensure_memu(report); ensure_vm3(report); ensure_kwai(report); ensure_historical_code(report); report['status']='COMPLETE'; report['finished_at']=now(); REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(report,ensure_ascii=False,indent=2)); return 0
 except Exception as exc:
  report['status']='FAILED'; report['error']=f"{type(exc).__name__}: {exc}"; report['finished_at']=now(); REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(report,ensure_ascii=False,indent=2)); return 1
if __name__=='__main__': raise SystemExit(main())
