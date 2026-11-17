#!/usr/bin/env python3
"""Publish only the pinned G5 ACF mapping manifest, preserving old metadata and write locks."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('anthares_bridge',here/'studio-g5g6-isolated-qa.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
REMOTE=r"""
import hashlib,os,pathlib,subprocess,tempfile
MODE='MODE_MARK'
home=pathlib.Path.home()
root=home/'domains/anthares.us/public_html/wp-content/plugins'
live=root/'anthares-studio'
legacy=root/'anthares-estudio/anthares-estudio.php'
source=home/'domains/anthares.us/anthares-private-storage/studio-g6-review-20261116'
name='docs/acf-core-migration-map.json'
target=live/name
def require(flag,code):
 if not flag:raise RuntimeError(code)
def gitsha(data):
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\x00'+data).hexdigest()
require(MODE in ('preflight','publish'),'INVALID_MODE')
require(live.is_dir() and not live.is_symlink() and source.is_dir(),'STUDIO_DIR_MISSING')
require(hashlib.sha256(legacy.read_bytes()).hexdigest()=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','ORIGINAL_CHANGED')
require(gitsha((live/'anthares-estudio.php').read_bytes())=='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb','INTEGRATION_PHP_CHANGED')
commit='3efad7ad3b41e765132f625202daad88f8f2ee7d'
p=subprocess.run(['git','-C',str(source),'show',commit+':anthares-studio/'+name],capture_output=True,timeout=18)
require(p.returncode==0,'MANIFEST_SOURCE_NOT_FOUND')
data=p.stdout
require(gitsha(data)=='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325','MANIFEST_BLOB_UNEXPECTED')
require(len(list((live/'acf-json').glob('group_anst*.json')))==12,'ACF_GROUPS_MISSING')
require((live/'includes/acf/class-anst-acf-repository.php').is_file(),'ACF_RUNTIME_CLASS_MISSING')
require((live/'includes/acf/class-anst-acf-migrator.php').is_file(),'ACF_MIGRATOR_CLASS_MISSING')
require(not target.is_symlink(),'MANIFEST_SYMLINK_FORBIDDEN')
if target.exists():require(target.read_bytes()==data,'EXISTING_MANIFEST_DIFFERENT')
print('STUDIO_G5_MANIFEST_PREFLIGHT=PASS',flush=True)
print('STUDIO_G5_ACF_GROUPS=12',flush=True)
if MODE=='publish':
 if not target.exists():
  target.parent.mkdir(parents=True,exist_ok=True)
  fd,temp=tempfile.mkstemp(prefix='.acf-map-',dir=target.parent)
  try:
   with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
   os.chmod(temp,0o644)
   os.replace(temp,target)
  finally:
   if os.path.exists(temp):os.unlink(temp)
 require(target.read_bytes()==data,'MANIFEST_COPY_CHECK_FAILED')
 require(hashlib.sha256(legacy.read_bytes()).hexdigest()=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_CHANGED_AFTER_MANIFEST')
 print('STUDIO_G5_MAP_DEPLOY_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 mode=os.getenv('STUDIO_G5_MAP_MODE','preflight')
 if mode not in ('preflight','publish'):raise RuntimeError('INVALID_MODE')
 key,host,port,user=mod.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='anthares-g5-manifest-') as temp:
  k=pathlib.Path(temp)/'key';k.write_text(key);k.chmod(0o600)
  hosts=pathlib.Path(temp)/'hosts';hosts.write_text('anthares-g5-map '+mod.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(hosts),
       '-o','HostKeyAlias=anthares-g5-map','-o','ConnectTimeout=12',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE.replace('MODE_MARK',mode),capture_output=True,text=True,timeout=80)
  for line in r.stdout.splitlines():
   if line.startswith('STUDIO_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('STUDIO_G5_MAP_FAILURE='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in last)[:120],flush=True)
   raise RuntimeError('REMOTE_MAP_FAILED')
  signal='STUDIO_G5_MAP_DEPLOY_PROVEN=1' if mode=='publish' else 'STUDIO_G5_MANIFEST_PREFLIGHT=PASS'
  if signal not in r.stdout:raise RuntimeError('MISSING_RESULT')
if __name__=='__main__':
 main()
