#!/usr/bin/env python3
"""Read-only WP-CLI G5 ACF migration dry run, requires verified site, never --apply."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g5_bridge',here/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import hashlib,pathlib,subprocess,re
home=pathlib.Path.home()
web=home/'domains/anthares.us/public_html'
plugin=web/'wp-content/plugins/anthares-studio'
private=home/'domains/anthares.us/anthares-private-storage'
manifest=plugin/'docs/acf-core-migration-map.json'
loader=plugin/'includes/acf/class-anst-acf-migrator.php'
php='/opt/alt/php83/usr/bin/php'
wp='/usr/local/bin/wp'
def check(b,label):
 if not b:raise RuntimeError(label)
def gitblob(p):
 d=p.read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
check(gitblob(plugin/'anthares-estudio.php')=='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb','UNEXPECTED_PLUGIN_VERSION')
check(manifest.is_file() and gitblob(manifest)=='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325','MANIFEST_HASH_CHANGED')
check(loader.is_file() and pathlib.Path(wp).is_file(),'MIGRATOR_NOT_AVAILABLE')
backup=private/'studio-g1-backup-20261116-1527'
index=(backup/'backup-sha256.txt').read_text()
check('RESTORE=PASS' in (backup/'restore-verification.txt').read_text(),'RESTORE_PROOF_MISSING')
for name in ('wordpress-consistent.sql.gz','anthares-estudio-original.tar.gz'):
 p=backup/name
 check(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()+'  '+name in index,'BACKUP_SHA_MISMATCH')
args=[php,wp,'--path='+str(web),'--skip-themes','--require='+str(loader),'anst-acf-migrate']
run=subprocess.run(args,capture_output=True,text=True,timeout=95)
keys=('SOURCE_COUNT=','SOURCE_META_COUNT=','SOURCE_FINGERPRINT=','ACF_TARGET_PRESENT=','ACF_TARGET_EXISTING=',
      'ZOOM_USER_COUNT=','ACF_COURSE_JSON_BYTES=','REFERENCE_ERRORS=')
report={}
for line in run.stdout.splitlines():
 if line.startswith(keys):
  k,v=line.split('=',1);report[k]=v
  print('G5_DRY_'+line,flush=True)
if run.returncode:
 last=(run.stderr.strip().splitlines() or ['NO_STDERR'])[-1]
 safe=''.join(c if c.isalnum() or c in ' _:./-=' else '_' for c in last)[:160]
 print('G5_DRY_FAIL_LAST='+safe,flush=True)
raise_check=run.returncode==0
check(raise_check,'ACF_DRY_RUN_FAILED')
check('DRY_RUN_ONLY' in run.stdout+run.stderr,'MISSING_DRY_RUN_SUCCESS')
check(report.get('SOURCE_COUNT')=='71','SOURCE_COUNT_UNEXPECTED')
check(report.get('REFERENCE_ERRORS')=='0','ACF_REFERENCES_INVALID')
check(len(report.get('SOURCE_FINGERPRINT',''))==64,'FINGERPRINT_INVALID')
check(int(report.get('ACF_TARGET_PRESENT','0'))>=400,'ACF_MAPPING_TOO_SMALL')
print('G5_DRY_RUN_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':
  raise RuntimeError('BRANCH_UNAUTHORIZED')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-dry-') as tmp:
  p=pathlib.Path(tmp);k=p/'key';k.write_text(key);k.chmod(0o600)
  h=p/'hosts';h.write_text('anthares-g5-live-dry '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-live-dry','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=130)
  for line in r.stdout.splitlines():
   if line.startswith('G5_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G5_DRY_ERROR='+''.join(x if x.isalnum() or x in ' _:.-' else '_' for x in last)[:120],flush=True)
   raise RuntimeError('G5_READONLY_DRYRUN_FAILED')
  if 'G5_DRY_RUN_PROVEN=1' not in r.stdout:raise RuntimeError('DRYRUN_SUCCESS_MISSING')
if __name__=='__main__':main()
