#!/usr/bin/env python3
"""Atomic, recoverable activation of G5 ACF read runtime after verified 414/414 migration."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g5_bridge',here/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import fcntl,hashlib,os,pathlib,subprocess,json,datetime
home=pathlib.Path.home()
web=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
plugin=web/'wp-content/plugins/anthares-studio'
legacy=web/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
BACKUP=private/'studio-g1-backup-20261116-1527'
SOURCE_FINGERPRINT='bced1ad06c27a43a25585d9663457dd2cdc2f4c58f24bb1dada8696defe10bd1'
NEW_PHP_BLOB='16f5c01457085e73fcde291717ba46ebdbdb2801'
MANIFEST_BLOB='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325'
LEGACY_SHA='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'
wp=['/opt/alt/php83/usr/bin/php','/usr/local/bin/wp','--path='+str(web),'--skip-themes']
def require(v,code):
 if not v:raise RuntimeError(code)
def blob(p):
 d=p.read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
def safe_check():
 require(blob(plugin/'anthares-estudio.php')==NEW_PHP_BLOB,'PLUGIN_VERSION_CHANGED')
 require(blob(plugin/'docs/acf-core-migration-map.json')==MANIFEST_BLOB,'ACF_MAP_CHANGED')
 require(hashlib.sha256(legacy.read_bytes()).hexdigest()==LEGACY_SHA,'ORIGINAL_PLUGIN_CHANGED')
 p=subprocess.run(wp+['eval',r'''global $wpdb;
$ct=function($prefix)use($wpdb){return (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('{$prefix}_projeto','{$prefix}_nota','{$prefix}_capitulo','{$prefix}_cartao')");};
$ok=$ct('aest')===71&&$ct('anst')===71&&
 (string)get_option('anst_writes_enabled','0')==='0'&&
 (string)get_option('anst_trash_cleanup_enabled','0')==='0';
WP_CLI::line('G5_LIVE_SAFETY='.(int)$ok);'''],capture_output=True,text=True,timeout=45)
 require(p.returncode==0 and 'G5_LIVE_SAFETY=1' in p.stdout,'PRODUCTION_FLAGS_OR_COUNTS_CHANGED')
def verify_backup():
 require(BACKUP.is_dir() and 'RESTORE=PASS' in (BACKUP/'restore-verification.txt').read_text(),'RESTORE_PROOF_UNAVAILABLE')
 idx=(BACKUP/'backup-sha256.txt').read_text()
 for filename in ('wordpress-consistent.sql.gz','anthares-estudio-original.tar.gz'):
  file=BACKUP/filename
  require(file.is_file(),'BACKUP_FILE_MISSING')
  digest=hashlib.sha256(file.read_bytes()).hexdigest()
  require(digest+'  '+filename in idx,'BACKUP_HASH_MISMATCH')
def migrate_dry():
 loader=plugin/'includes/acf/class-anst-acf-migrator.php'
 cmd=wp[:]+['--require='+str(loader),'anst-acf-migrate']
 p=subprocess.run(cmd,text=True,capture_output=True,timeout=75)
 require(p.returncode==0 and 'DRY_RUN_ONLY' in p.stdout+p.stderr,'MIGRATOR_DRYRUN_FAILED')
 out={a:b for line in p.stdout.splitlines() if '=' in line for a,b in [line.split('=',1)]}
 for k,v in [('SOURCE_COUNT','71'),('SOURCE_FINGERPRINT',SOURCE_FINGERPRINT),
             ('ACF_TARGET_PRESENT','412'),('ACF_TARGET_EXISTING','414'),
             ('REFERENCE_ERRORS','0'),('ZOOM_USER_COUNT','1')]:
  require(out.get(k)==v,'MIGRATOR_SOURCE_DRIFT_'+k)
def bootstrap(mode):
 PHP=r'''global $wpdb;
$mode='MODE_VALUE';
$owners=$wpdb->get_col("SELECT DISTINCT post_author FROM {$wpdb->posts} WHERE post_type IN ('anst_projeto','anst_nota','anst_capitulo','anst_cartao') ORDER BY post_author");
if(count($owners)!==2) WP_CLI::error('OWNER_COUNT_CHANGED');
$enabled=anst_acf_runtime_enabled();
if ($enabled!==($mode==='ON')) WP_CLI::error('ACF_MODE_MISMATCH');
if ($mode==='ON') {
 $total=0;
 foreach (acf_get_local_field_groups() as $g)if(str_starts_with((string)($g['key']??''),'group_anst'))$total++;
 if ($total!==12)WP_CLI::error('ACF_GROUPS_NOT_LOADED');
}
$result=[];
foreach($owners as $id){
 wp_set_current_user((int)$id);
 $r=anst_bootstrap(new WP_REST_Request('GET','/anthares-studio/v1/bootstrap'));
 if(is_wp_error($r))WP_CLI::error('BOOTSTRAP_RESPONSE_ERROR');
 $json=wp_json_encode($r->get_data(),JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
 if(!is_string($json))WP_CLI::error('BOOTSTRAP_JSON_FAILED');
 $result[]=hash('sha256',$json);
}
WP_CLI::line('G5_BOOTSTRAP_DIGEST='.hash('sha256',implode('|',$result)));
WP_CLI::line('G5_BOOTSTRAP_USERS='.count($owners));
WP_CLI::line('G5_BOOTSTRAP_MODE='.$mode);
'''
 PHP=PHP.replace('MODE_VALUE',mode)
 p=subprocess.run(wp+['eval',PHP],text=True,capture_output=True,timeout=75)
 if p.returncode:
  tail=(p.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
  tail=''.join(c if c.isalnum() or c in ' _:.-=' else '_' for c in tail)[:140]
  print('G5_ACTIVATION_BOOTSTRAP_FAILURE='+tail,flush=True)
 require(p.returncode==0,'BOOTSTRAP_FAILED_'+mode)
 data={line.split('=',1)[0]:line.split('=',1)[1] for line in p.stdout.splitlines() if line.startswith('G5_BOOTSTRAP_') and '=' in line}
 require(data.get('G5_BOOTSTRAP_USERS')=='2','BOOTSTRAP_OWNER_ERROR')
 require(data.get('G5_BOOTSTRAP_MODE')==mode,'BOOTSTRAP_WRONG_MODE')
 require(len(data.get('G5_BOOTSTRAP_DIGEST',''))==64,'BOOTSTRAP_DIGEST_MISSING')
 return data['G5_BOOTSTRAP_DIGEST']
def option_read(emergency=False):
 args=wp[:]
 if emergency:args.append('--skip-plugins')
 p=subprocess.run(args+['eval',"WP_CLI::line('G5_OPTION='.get_option('anst_acf_runtime_enabled','__ABSENT__'));"],
                  text=True,capture_output=True,timeout=45)
 require(p.returncode==0,'ACF_OPTION_READ_FAILED')
 value=next((v.split('=',1)[1] for v in p.stdout.splitlines() if v.startswith('G5_OPTION=')),None)
 require(value in ('0','1','__ABSENT__'),'ACF_OPTION_VALUE_UNEXPECTED')
 return value
def write_option(value,emergency=False):
 args=wp[:]
 if emergency:args.append('--skip-plugins')
 r=subprocess.run(args+['option','update','anst_acf_runtime_enabled',value],
                  text=True,capture_output=True,timeout=55)
 require(r.returncode==0,'ACF_OPTION_UPDATE_FAILED_'+value)
def restore_option(original):
 args=wp+['--skip-plugins']
 if original=='__ABSENT__':
  cmd=args+['option','delete','anst_acf_runtime_enabled']
 else:
  cmd=args+['option','update','anst_acf_runtime_enabled',original]
 r=subprocess.run(cmd,text=True,capture_output=True,timeout=55)
 require(r.returncode==0,'ACF_OPTION_ROLLBACK_COMMAND_FAILED')
 require(option_read(emergency=True)==original,'ACF_OPTION_ROLLBACK_MISMATCH')
lock_path=private/'.studio-g5-runtime-activation.lock'
with open(lock_path,'a+') as handle:
 try:fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise RuntimeError('ACF_ACTIVATION_BUSY')
 safe_check()
 verify_backup()
 original=option_read()
 require(original in ('0','__ABSENT__'),'ACF_RUNTIME_OPTION_ALREADY_CHANGED')
 migrate_dry()
 before=bootstrap('OFF')
 backup=private/('studio-g5-option-rollback-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
 require(not backup.exists(),'OPTION_BACKUP_PATH_EXISTS')
 backup.mkdir(mode=0o700)
 (backup/'state.txt').write_text('ACF_OPTION_BEFORE='+original+'\nLEGACY_71=71\nACF_71=71\nSOURCE_SHA='+SOURCE_FINGERPRINT+'\n')
 os.chmod(backup/'state.txt',0o600)
 activated=False
 try:
  write_option('1')
  activated=True
  require(option_read()=='1','ACF_OPTION_PERSISTENCE_FAILED')
  after=bootstrap('ON')
  require(after==before,'ACF_BOOTSTRAP_CONTENT_CHANGED')
  safe_check()
  migrate_dry()
  require(option_read()=='1','ACF_OPTION_CONCURRENT_CHANGE')
  print('G5_ACF_RUNTIME_LIVE=ON',flush=True)
  print('G5_BOOTSTRAP_OWNERS_MATCH=2',flush=True)
  print('G5_SOURCE_71_MATCH=1',flush=True)
  print('G5_ACF_414_MATCH=1',flush=True)
  print('G5_WRITES_STILL_OFF=1',flush=True)
  print('G5_ORIGINAL_PLUGIN_UNCHANGED=1',flush=True)
  print('G5_OPTION_BACKUP_NAME='+backup.name,flush=True)
  print('G5_ACF_PRODUCTION_ACTIVATION_PROVEN=1',flush=True)
 except Exception as e:
  if activated:
   restore_option(original)
   print('G5_RUNTIME_ACTIVATION_ROLLBACK=COMPLETE',flush=True)
  raise
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-live-toggle-') as tmp:
  d=pathlib.Path(tmp);k=d/'key';k.write_text(key);k.chmod(0o600)
  h=d/'hosts';h.write_text('anthares-g5-runtime-toggle '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-runtime-toggle','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=300)
  for line in r.stdout.splitlines():
   if line.startswith('G5_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G5_ACTIVATION_REMOTE_ERROR='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in last)[:130],flush=True)
   raise RuntimeError('G5_RUNTIME_ACTIVATION_FAILED')
  if 'G5_ACF_PRODUCTION_ACTIVATION_PROVEN=1' not in r.stdout:
   raise RuntimeError('G5_ACTIVATION_SUCCESS_MISSING')
if __name__=='__main__':main()
