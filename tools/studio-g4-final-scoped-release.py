#!/usr/bin/env python3
"""G4 code-only release with independent backup and reversible ACF OFF/ON pause."""
import base64,hashlib,importlib.util,io,os,pathlib,subprocess,tarfile,tempfile,zlib
HERE=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('g4_bridge',HERE/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(sp);sp.loader.exec_module(bridge)
APPROVED={
 'anthares-estudio.php':'8a9becf2da9da692bfecaa508591f9fb33f30780',
 'assets/estudio.js':'18669c8fa7f24efcacc9c040145ecc0c7fa4db03',
 'acf-json/group_anst02_v1.json':'e52490e072f6cb14e8f270f62962e178e39c8e77',
 'docs/acf-core-migration-map.json':'e4eed3976171510c2d4146eee04c38ed6ae2fc4f',
 'includes/acf/class-anst-acf-repository.php':'52075b6d0ce8906058ea24579c190a305e2f7ce6',
 'includes/acf/class-anst-acf-migrator.php':'286697cc7f2f9afcbcafcd8a52147aa9273f8602'
}
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def package():
 bf=io.BytesIO()
 with tarfile.open(fileobj=bf,mode='w:gz') as z:
  for rel,sha in APPROVED.items():
   p=HERE/'studio-g4-approved'/rel
   if not p.is_file() or blob(p.read_bytes())!=sha:raise RuntimeError('LOCAL_SOURCE_BLOB_CHANGED_'+rel)
   payload=p.read_bytes()
   meta=tarfile.TarInfo(name=rel);meta.size=len(payload);meta.mode=0o600
   z.addfile(meta,io.BytesIO(payload))
 return base64.b64encode(bf.getvalue()).decode()
REMOTE=r"""
import base64,datetime,fcntl,hashlib,io,json,os,pathlib,shutil,stat,subprocess,sys,tarfile,tempfile
MODE='MODE_MARKER'
RAW=base64.b64decode('PAYLOAD_MARKER')
EXPECTED=json.loads('JSON_EXPECTED_MARKER')
base=pathlib.Path.home()/'domains/anthares.us'
root=base/'public_html'
private=base/'anthares-private-storage'
live=root/'wp-content/plugins/anthares-studio'
original=root/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
source=private/'studio-g6-review-20261116'
php='/opt/alt/php83/usr/bin/php'
wp=[php,'/usr/local/bin/wp','--path='+str(root),'--skip-themes']
OLD_PHP='16f5c01457085e73fcde291717ba46ebdbdb2801'
LEGACY_SHA256='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'
OLD_MAP='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325'
def check(ok,msg):
 if not ok:raise RuntimeError(msg)
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def stage():
 buf=io.BytesIO(RAW)
 files={}
 with tarfile.open(fileobj=buf,mode='r:gz') as tar:
  members=tar.getmembers()
  check(len(members)==len(EXPECTED),'UNEXPECTED_FILE_COUNT')
  for m in members:
   check(m.isfile() and not m.issym() and not m.islnk() and
     not m.name.startswith('/') and '..' not in pathlib.PurePosixPath(m.name).parts,'BAD_TAR_ITEM')
   check(m.name in EXPECTED,'UNEXPECTED_PACKAGE_PATH')
   data=tar.extractfile(m).read()
   check(blob(data)==EXPECTED[m.name],'EXPECTED_PATCH_BLOB_MISMATCH')
   files[m.name]=data
 check(set(files)==set(EXPECTED),'UNEXPECTED_PATCH_CONTENTS')
 return files
def option():
 proc=subprocess.run(wp+['--skip-plugins','eval',"WP_CLI::line('FLAG='.get_option('anst_acf_runtime_enabled','0'));"],
                      capture_output=True,text=True,timeout=40)
 check(proc.returncode==0,'RUNTIME_OPTION_READ_FAILED')
 return next((x.split('=',1)[1] for x in proc.stdout.splitlines() if x.startswith('FLAG=')),None)
def update_option(v):
 proc=subprocess.run(wp+['--skip-plugins','option','update','anst_acf_runtime_enabled',v],
                     capture_output=True,text=True,timeout=40)
 check(proc.returncode==0,'RUNTIME_OPTION_UPDATE_FAILED')
 check(option()==v,'RUNTIME_OPTION_PERSISTENCE_FAILED')
def state(expect_runtime='1'):
 code=r'''define("DISABLE_WP_CRON",true);require "WP_LOAD";
global $wpdb;
$counter=function($n)use($wpdb){return (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('{$n}_projeto','{$n}_nota','{$n}_capitulo','{$n}_cartao')");};
$ok=$counter('aest')===71&&$counter('anst')===71&&
 (string)get_option('anst_writes_enabled','0')==='0'&&
 (string)get_option('anst_trash_cleanup_enabled','0')==='0'&&
 (string)get_option('anst_acf_runtime_enabled','0')==='RUNTIME_FLAG';
echo 'G4_GATE_STATE='.(int)$ok."\n";'''
 code=code.replace('WP_LOAD',str(root/'wp-load.php')).replace('RUNTIME_FLAG',expect_runtime)
 proc=subprocess.run([php,'-r',code],capture_output=True,text=True,timeout=45)
 check(proc.returncode==0 and 'G4_GATE_STATE=1' in proc.stdout,'WP_RUNTIME_STATE_UNEXPECTED')
 check(hashlib.sha256(original.read_bytes()).hexdigest()==LEGACY_SHA256,'ORIGINAL_CHANGED')
def check_old_sources():
 check(live.is_dir() and not live.is_symlink(),'LIVE_PLUGIN_PATH_CHANGED')
 check(source.is_dir(),'REVIEW_SOURCE_MISSING')
 head=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=10).strip()
 check(head=='3efad7ad3b41e765132f625202daad88f8f2ee7d','REVIEW_SOURCE_HEAD_CHANGED')
 for rel in EXPECTED:
  livefile=live/rel
  check(livefile.is_file() and not livefile.is_symlink(),'LIVE_MISSING_'+rel)
  actual=livefile.read_bytes()
  if rel=='anthares-estudio.php':
   check(blob(actual)==OLD_PHP,'LIVE_MAIN_CHANGED')
  else:
   original=subprocess.run(['git','-C',str(source),'show','HEAD:anthares-studio/'+rel],
                           capture_output=True,timeout=15)
   check(original.returncode==0,'BASE_SOURCE_MISSING_'+rel)
   check(actual==original.stdout,'CONCURRENT_LIVE_CHANGE_'+rel)
 check(blob((live/'docs/acf-core-migration-map.json').read_bytes())==OLD_MAP,'OLD_MAPPING_CHANGED')
def lint_all(files):
 for rel,payload in files.items():
  if rel.endswith('.php'):
   p=subprocess.run([php,'-l'],input=payload,capture_output=True,timeout=15)
   check(p.returncode==0,'PATCH_PHP_LINT_'+rel)
def write_atomic(path,payload,mode=0o644):
 fd,name=tempfile.mkstemp(prefix='.anst-g4-final-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'wb') as w:w.write(payload);w.flush();os.fsync(w.fileno())
  os.chmod(name,mode);os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
def live_probe():
 # Confirm all new ACF definitions are accessible and that the original 414 values remain unchanged.
 cmd=wp+['eval',r'''global $wpdb;
if(!anst_acf_runtime_enabled())WP_CLI::error('G4_ACF_RUNTIME_OFF');
$map=anst_acf_field_map();
if(!isset($map['anst_projeto']['_anst_events']))WP_CLI::error('EVENT_FIELD_NOT_MAPPED');
$groups=0;foreach(acf_get_local_field_groups() as $g){if(str_starts_with((string)($g['key']??''),'group_anst'))$groups++;}
if($groups!==12)WP_CLI::error('GROUP_COUNT_CHANGED');
$owners=$wpdb->get_col("SELECT DISTINCT post_author FROM {$wpdb->posts} WHERE post_type='anst_projeto' AND post_status='publish' ORDER BY post_author");
if(count($owners)!==2)WP_CLI::error('OWNERS_CHANGED');
foreach($owners as $uid){
 wp_set_current_user((int)$uid);
 $r=anst_bootstrap(new WP_REST_Request('GET','/anthares-studio/v1/bootstrap'));
 if(is_wp_error($r))WP_CLI::error('BOOTSTRAP_FAILED');
}
WP_CLI::line('G4_LIVE_READONLY_ACF_PROBE=PASS');''']
 proc=subprocess.run(cmd,capture_output=True,text=True,timeout=75)
 check(proc.returncode==0 and 'G4_LIVE_READONLY_ACF_PROBE=PASS' in proc.stdout,
       'NEW_ACF_LIVE_CANARY_FAILED')
 # Historical manifest has 414 values: run dry-run with new 40/52 contract.
 cmd=wp+['--require='+str(live/'includes/acf/class-anst-acf-migrator.php'),'anst-acf-migrate']
 proc=subprocess.run(cmd,text=True,capture_output=True,timeout=70)
 check(proc.returncode==0 and 'DRY_RUN_ONLY' in proc.stdout+proc.stderr,'G4_NEW_ACF_DRYRUN_FAILED')
 out={x.split('=',1)[0]:x.split('=',1)[1] for x in proc.stdout.splitlines() if '=' in x}
 for k,v in [('SOURCE_COUNT','71'),('SOURCE_META_COUNT','412'),('ACF_TARGET_EXISTING','414'),
             ('REFERENCE_ERRORS','0')]:
  check(out.get(k)==v,'G4_LIVE_ACF_SOURCE_MISMATCH_'+k)
 print('G4_LIVE_ACF_40_FIELDS_52_MAPPINGS_AND_414_VALUES=PASS',flush=True)
check(MODE in ('preflight','deploy'),'INVALID_MODE')
files=stage();lint_all(files)
lock_path=private/'.studio-g4-final-release.lock'
with open(lock_path,'a+') as lock:
 try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise RuntimeError('G4_RELEASE_LOCK_BUSY')
 state('1')
 check(option()=='1','G4_ACF_MODE_UNEXPECTED')
 check_old_sources()
 print('G4_RELEASE_PRECHECK=PASS',flush=True)
 print('G4_RELEASE_FILES='+str(len(files)),flush=True)
 if MODE=='preflight':
  print('G4_RELEASE_PREFLIGHT_PROVEN=1',flush=True)
 else:
  backup=private/('studio-g4-final-backup-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
  check(not backup.exists(),'BACKUP_NAME_COLLISION')
  backup.mkdir(mode=0o700)
  copies={}
  for rel in files:
   src=live/rel
   copies[rel]=src.read_bytes()
   dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(copies[rel]);os.chmod(dest,0o600)
   check(dest.read_bytes()==copies[rel],'BACKUP_COPY_MISMATCH')
  manifest={rel:{'before':blob(copies[rel]),'after':EXPECTED[rel]} for rel in files}
  (backup/'release-manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2))
  os.chmod(backup/'release-manifest.json',0o600)
  changed=[]
  disabled=False
  try:
   update_option('0');disabled=True
   state('0')
   for rel in sorted(files,key=lambda x:(x=='anthares-estudio.php',x)):
    target=live/rel
    check(blob(target.read_bytes())==manifest[rel]['before'],'CONCURRENT_MUTATION_'+rel)
    write_atomic(target,files[rel],0o644)
    changed.append(rel)
   for rel in files:check(blob((live/rel).read_bytes())==EXPECTED[rel],'AFTER_WRITE_SHA_MISMATCH_'+rel)
   state('0')
   update_option('1')
   state('1')
   live_probe()
   print('G4_RELEASE_PRODUCTION_CODE_DEPLOYED=1',flush=True)
   print('G4_RELEASE_ACF_RUNTIME_ON=1',flush=True)
   print('G4_RELEASE_WRITES_STILL_OFF=1',flush=True)
   print('G4_RELEASE_LEGACY_UNCHANGED=1',flush=True)
   print('G4_RELEASE_BACKUP_NAME='+backup.name,flush=True)
  except BaseException as e:
   print('G4_RELEASE_ABORT_REASON='+str(e)[:150],flush=True)
   try:
    if option()=='1':update_option('0')
    for rel in reversed(changed):
     target=live/rel;write_atomic(target,copies[rel],0o644)
    for rel in copies:check(blob((live/rel).read_bytes())==manifest[rel]['before'],'ROLLBACK_FILE_MISMATCH_'+rel)
    if disabled:update_option('1')
    state('1')
    print('G4_RELEASE_ROLLBACK_PROVEN=1',flush=True)
   except Exception as err:
    print('G4_RELEASE_ROLLBACK_FAILED='+str(err)[:140],flush=True)
   raise
"""
def main():
 if os.environ.get('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('BRANCH_UNAPPROVED')
 mode=os.getenv('G4_RELEASE_MODE','preflight')
 if mode not in ('preflight','deploy'):raise RuntimeError('MODE_INVALID')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g4-final-deploy-') as tmp:
  d=pathlib.Path(tmp);k=d/'key';k.write_text(key);k.chmod(0o600)
  h=d/'hosts';h.write_text('anthares-g4-final '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','BatchMode=yes','-o','IdentitiesOnly=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g4-final','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  payload=REMOTE.replace('MODE_MARKER',mode).replace('JSON_EXPECTED_MARKER',json.dumps(APPROVED))
  payload=payload.replace('PAYLOAD_MARKER',package())
  p=subprocess.run(cmd,input=payload,text=True,capture_output=True,timeout=210)
  for line in p.stdout.splitlines():
   if line.startswith('G4_'):print(line,flush=True)
  if p.returncode:
   last=(p.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   safe=''.join(c if c.isalnum() or c in ' _:.-' else '_' for c in last)[:150]
   print('G4_RELEASE_REMOTE_ERROR='+safe,flush=True)
   raise RuntimeError('SCOPED_RELEASE_FAILED')
  marker='G4_RELEASE_PREFLIGHT_PROVEN=1' if mode=='preflight' else 'G4_RELEASE_PRODUCTION_CODE_DEPLOYED=1'
  if marker not in p.stdout:raise RuntimeError('RELEASE_SUCCESS_MARKER_MISSING')
if __name__=='__main__':
 import json
 main()
