#!/usr/bin/env python3
"""G4 final gate: permit authorized writes to isolated /studio only after full acceptance.
Never modifies historical posts. Saves option state and rolls it back on failure.
"""
import importlib.util,os,pathlib,subprocess,tempfile
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g4_bridge',HERE/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import datetime,fcntl,hashlib,json,os,pathlib,subprocess,sys
MODE='MODE_MARKER'
home=pathlib.Path.home();public=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
plugin=public/'wp-content/plugins/anthares-studio'
legacy=public/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
php='/opt/alt/php83/usr/bin/php';cli='/usr/local/bin/wp'
cmd=[php,cli,'--path='+str(public),'--skip-themes']
expected={
 'anthares-estudio.php':'8a9becf2da9da692bfecaa508591f9fb33f30780',
 'assets/estudio.js':'18669c8fa7f24efcacc9c040145ecc0c7fa4db03',
 'acf-json/group_anst02_v1.json':'e52490e072f6cb14e8f270f62962e178e39c8e77',
 'docs/acf-core-migration-map.json':'e4eed3976171510c2d4146eee04c38ed6ae2fc4f',
 'includes/acf/class-anst-acf-repository.php':'52075b6d0ce8906058ea24579c190a305e2f7ce6',
 'includes/acf/class-anst-acf-migrator.php':'286697cc7f2f9afcbcafcd8a52147aa9273f8602'}
def check(b,msg):
 if not b:raise RuntimeError(msg)
def blob(p):
 d=p.read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\x00'+d).hexdigest()
def command(argv,limit=65):
 r=subprocess.run(argv,text=True,capture_output=True,timeout=limit)
 if r.returncode:
  err=(r.stderr.strip().splitlines() or ['NO_STDERR'])[-1]
  err=''.join(x if x.isalnum() or x in ' _:.=-' else '_' for x in err)[:100]
  print('G4_GATE_WP_ERROR='+err,flush=True)
 check(r.returncode==0,'WP_CLI_FAILED')
 return r.stdout
def read_option():
 code="WP_CLI::line('G4_READ_FLAG='.get_option('anst_writes_enabled','__ABSENT__'));"
 out=command(cmd+['--skip-plugins','eval',code])
 value=next((line.split('=',1)[1] for line in out.splitlines() if line.startswith('G4_READ_FLAG=')),None)
 check(value in ('0','1','__ABSENT__'),'WRITE_FLAG_READ_UNEXPECTED')
 return value
def set_option(value):
 if value=='__ABSENT__':
  command(cmd+['--skip-plugins','option','delete','anst_writes_enabled'])
 else:
  command(cmd+['--skip-plugins','option','update','anst_writes_enabled',value])
 check(read_option()==value,'WRITE_FLAG_PERSISTENCE_FAILED')
def site_assert(expected_write):
 PHP=r'''global $wpdb;
$count=function($prefix)use($wpdb){
 $sql="SELECT post_status,COUNT(*) n FROM {$wpdb->posts} WHERE post_type IN ('{$prefix}_projeto','{$prefix}_nota','{$prefix}_capitulo','{$prefix}_cartao') GROUP BY post_status";
 $out=['publish'=>0,'trash'=>0];foreach($wpdb->get_results($sql,ARRAY_A) as $v)if(isset($out[$v['post_status']]))$out[$v['post_status']]=(int)$v['n'];
 return $out;};
$old=$count('aest');$new=$count('anst');
function g4test($ok,$why){if(!$ok)WP_CLI::error('G4_GATE_'+$why);}
g4test($old===$new&&$old['publish']===40&&$old['trash']===31,'DATA_DRIFT');
g4test((string)get_option('anst_writes_enabled','0')==='EXPECTED_WRITE','FLAG_DRIFT');
g4test((string)get_option('anst_trash_cleanup_enabled','0')==='0','TRASH_CLEANUP_ENABLED');
g4test(anst_acf_runtime_enabled(),'ACF_RUNTIME_OFF');
g4test(count(acf_get_local_field_groups())>=12,'ACF_GROUPS_MISSING');
$page=get_page_by_path('studio',OBJECT,'page');
g4test($page instanceof WP_Post&&$page->post_status==='private','STUDIO_NOT_PRIVATE');
$authors=$wpdb->get_col("SELECT DISTINCT post_author FROM {$wpdb->posts} WHERE post_type='anst_projeto' AND post_status='publish' ORDER BY post_author");
g4test(count($authors)===2,'OWNERS_CHANGED');
$approved=0;
foreach($authors as $author){
 wp_set_current_user((int)$author);
 if(!anst_can_use())continue;
 $approved++;
 $request=new WP_REST_Request('POST','/anthares-studio/v1/projects');
 $permission=anst_permission($request);
 if('EXPECTED_WRITE'==='1'){
  g4test($permission===true,'AUTH_OWNER_WRITE_REFUSED');
  $request->set_param('mode','__invalid_g4_probe');
  $request->set_param('title','No writing expected');
  rest_get_server();
  $response=rest_do_request($request);
  g4test($response instanceof WP_REST_Response&&$response->get_status()===400 &&
         ($response->get_data()['code']??'')==='anst_mode','AUTHORIZED_REST_ERROR_PATH_WRONG');
 }else{
  g4test(is_wp_error($permission)&&($permission->get_error_data()['status']??0)===423,'WRITE_LOCK_INVALID');
 }
}
g4test($approved>=1,'NO_AUTHORIZED_WRITER');
wp_set_current_user(0);
g4test(anst_permission(new WP_REST_Request('POST','/anthares-studio/v1/projects'))===false,'ANONYMOUS_WRITE_LEAK');
WP_CLI::line('G4_GATE_LIVE_POSTS_UNMODIFIED=1');
WP_CLI::line('G4_GATE_REST_AUTHZ_CONFIRMED=1');
WP_CLI::line('G4_GATE_ACF_ON_AND_PRIVATE=1');
WP_CLI::line('G4_GATE_RUNTIME_EXPECTED=EXPECTED_WRITE');
'''
 PHP=PHP.replace('EXPECTED_WRITE',expected_write)
 out=command(cmd+['eval',PHP],limit=95)
 check('G4_GATE_LIVE_POSTS_UNMODIFIED=1' in out and 'G4_GATE_RUNTIME_EXPECTED='+expected_write in out,'RESPONSE_PROOF_MISSING')
 for line in out.splitlines():
  if line.startswith('G4_GATE_'):print(line,flush=True)
def verify_artifacts():
 check(plugin.is_dir() and not plugin.is_symlink() and private.is_dir(),'STUDIO_PATH_CHANGED')
 check(legacy.is_file() and hashlib.sha256(legacy.read_bytes()).hexdigest()=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_CHANGED')
 for name,digest in expected.items():
  check(blob(plugin/name)==digest,'STUDIO_CODE_CHANGED_'+name.replace('/','_'))
 backup=private/'studio-g4-final-backup-20261117T143339Z'
 manifest=json.loads((backup/'release-manifest.json').read_text())
 check(set(expected)==set(manifest) and all(manifest[n]['after']==digest for n,digest in expected.items()),'APPROVED_BACKUP_CHANGED')
 # Restore-tested G1 backup is additionally required for data protection.
 g1=private/'studio-g1-backup-20261116-1527'
 check((g1/'wordpress-consistent.sql.gz').is_file() and 'RESTORE=PASS' in (g1/'restore-verification.txt').read_text(),'DATABASE_BACKUP_UNAVAILABLE')
 print('G4_GATE_CODE_BACKUP_AND_ORIGINAL=PASS',flush=True)
check(MODE in ('preflight','enable'),'UNEXPECTED_GATE_MODE')
lock=private/'.studio-g4-write-activation.lock'
with open(lock,'a+') as f:
 try:fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise RuntimeError('G4_WRITE_GATE_RUNNING')
 verify_artifacts()
 before=read_option()
 check(before in ('0','__ABSENT__'),'WRITE_GATE_STATE_CHANGED')
 site_assert('0')
 print('G4_WRITE_PREFLIGHT_PASS=1',flush=True)
 if MODE=='enable':
  backup=private/('studio-g4-write-activation-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
  check(not backup.exists(),'WRITE_GATE_BACKUP_COLLISION')
  backup.mkdir(mode=0o700)
  record=backup/'rollback-state.txt'
  record.write_text('OPTION_BEFORE='+before+'\nWRITE_TARGET=1\nDATA_POSTS_OLD=71\nDATA_POSTS_NEW=71\nBACKUP=studio-g1-backup-20261116-1527\n')
  os.chmod(record,0o600)
  activated=False
  try:
   set_option('1');activated=True
   site_assert('1')
   verify_artifacts()
   print('G4_WRITE_ENABLED_NEW_STUDIO=1',flush=True)
   print('G4_TRASH_CLEANUP_REMAINS_OFF=1',flush=True)
   print('G4_PRIVACY_AND_ACF_ON=1',flush=True)
   print('G4_OLD_STUDIO_UNCHANGED=1',flush=True)
   print('G4_WRITE_ROLLBACK_NAME='+backup.name,flush=True)
   print('G4_WRITE_ACTIVATION_PROVEN=1',flush=True)
  except BaseException:
   if activated:
    set_option(before)
    site_assert('0')
    print('G4_WRITE_ACTIVATION_ROLLBACK=PASS',flush=True)
   raise
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('BRANCH_NOT_AUTHORIZED')
 mode=os.getenv('G4_GATE_MODE','preflight')
 if mode not in ('preflight','enable'):raise RuntimeError('MODE_NOT_AUTHORIZED')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='anthares-studio-g4-writes-') as work:
  p=pathlib.Path(work);k=p/'key';k.write_text(key);k.chmod(0o600)
  hosts=p/'hosts';hosts.write_text('anthares-g4-write-activation '+bridge.HOST_KEY+'\n')
  ssh=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(hosts),
       '-o','HostKeyAlias=anthares-g4-write-activation','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  p=subprocess.run(ssh,input=REMOTE.replace('MODE_MARKER',mode),text=True,capture_output=True,timeout=205)
  for line in p.stdout.splitlines():
   if line.startswith('G4_'):print(line,flush=True)
  if p.returncode:
   last=(p.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G4_WRITE_REMOTE_ERROR='+''.join(c if c.isalnum() or c in ' _.:=-' else '_' for c in last)[:150],flush=True)
   raise RuntimeError('G4_WRITE_ACTIVATION_FAILED')
  marker='G4_WRITE_PREFLIGHT_PASS=1' if mode=='preflight' else 'G4_WRITE_ACTIVATION_PROVEN=1'
  if marker not in p.stdout:raise RuntimeError('G4_WRITE_EXPECTED_MARKER_MISSING')
if __name__=='__main__':main()
