#!/usr/bin/env python3
"""G5 new Studio ACF runtime rollout: dual gate, backup, GET-only owner parity, rollback."""
import importlib.util,os,pathlib,subprocess,tempfile
base=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('anthares_ssh_bridge',base/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import datetime,hashlib,json,os,pathlib,re,stat,subprocess,sys,tempfile
MODE='MODE_FIELD'
home=pathlib.Path.home()
site=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
plug=site/'wp-content/plugins/anthares-studio'
php=plug/'anthares-estudio.php'
legacy=site/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
manifest=plug/'docs/acf-core-migration-map.json'
cli='/opt/alt/php83/usr/bin/php'
wp='/usr/local/bin/wp'
ORIGINAL_SHA='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'
BEFORE_BLOB='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb'
AFTER_BLOB='16f5c01457085e73fcde291717ba46ebdbdb2801'
MAP_BLOB='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325'
def require(flag,code):
 if not flag:raise RuntimeError(code)
def gitblob(data):
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def php_cli(code):
 cmd=[cli,wp,'--path='+str(site),'--skip-themes','--no-color','eval',code]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 if p.returncode:
  kind='WP_CLI_PROCESS_ERROR'
  if 'Fatal error' in p.stderr:kind='WORDPRESS_FATAL'
  if 'Error:' in p.stderr:kind='WP_CLI_COMMAND_FAILED'
  print('STUDIO_RUNTIME_CLI_ERROR='+kind,flush=True)
  raise RuntimeError(kind)
 return p.stdout
def state(require_on=None):
 evalcode=r'''global $wpdb;
$k=['aest_projeto','aest_nota','aest_capitulo','aest_cartao'];
$j=['anst_projeto','anst_nota','anst_capitulo','anst_cartao'];
$types=fn($a)=>"'" . implode("','",$a) . "'";
$count=fn($types,$status)=> (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN (".$types.") AND post_status=".$wpdb->prepare("%s",$status));
$out=[
'old'=>$count($types($k),'publish')+$count($types($k),'trash'),
'new'=>$count($types($j),'publish')+$count($types($j),'trash'),
'old_live'=>$count($types($k),'publish'),'new_live'=>$count($types($j),'publish'),
'old_trash'=>$count($types($k),'trash'),'new_trash'=>$count($types($j),'trash'),
'writes'=>(string)get_option('anst_writes_enabled','0'),
'cleanup'=>(string)get_option('anst_trash_cleanup_enabled','0'),
'acf'=>(string)get_option('anst_acf_runtime_enabled','0'),
'page'=>(get_page_by_path('studio',OBJECT,'page')->post_status??''),
'acf_ready'=>function_exists('get_field')&&function_exists('anst_acf_runtime_enabled')&&anst_acf_runtime_enabled()
];
echo 'ANST_STATE='.wp_json_encode($out)."\n";'''
 output=php_cli(evalcode)
 line=next((s.split('=',1)[1] for s in output.splitlines() if s.startswith('ANST_STATE=')),None)
 require(bool(line),'WORDPRESS_STATE_ABSENT')
 obj=json.loads(line)
 require(obj['old']==71 and obj['new']==71 and obj['old_live']==40 and obj['new_live']==40 and obj['old_trash']==31 and obj['new_trash']==31,'WORDPRESS_71_COUNTS_DRIFT')
 require(obj['writes']=='0' and obj['cleanup']=='0' and obj['page']=='private','WORDPRESS_LOCK_OR_VISIBILITY_CHANGED')
 if require_on is not None:
  expected='1' if require_on else '0'
  require(obj['acf']==expected,'ACF_RUNTIME_FLAG_UNEXPECTED')
  require(obj['acf_ready'] is bool(require_on),'ACF_GATE_STATUS_INCONSISTENT')
 return obj
def option_update(value):
 phpcode="update_option('anst_acf_runtime_enabled',"+repr(value)+",false);wp_cache_flush();echo 'ACF_OPTION_UPDATED=1';"
 p=php_cli(phpcode)
 require('ACF_OPTION_UPDATED=1' in p,'OPTION_UPDATE_NOT_CONFIRMED')
def full_read_parity():
 script=r'''
global $wpdb;
if(!anst_acf_runtime_enabled())throw new Exception('ACF_GATE_NOT_ON');
if((string)get_option('anst_writes_enabled','0')!=='0')throw new Exception('WRITES_UNEXPECTED');
foreach(['field_anst01_start_mode_v1','field_anst07_chapter_delta_json_v1','field_anst16c_course_lesson_links_json_v1'] as $key)
 if(!acf_get_field($key))throw new Exception('ACF_SCHEMA_UNREGISTERED');
if(anst_acf_lesson_option_get()!==(array)get_option('anst_section_lesson_videos',[]))throw new Exception('ACF_COURSE_DIFF');
$rows=$wpdb->get_results("SELECT p.ID,m.meta_value FROM {$wpdb->posts} p JOIN {$wpdb->postmeta} m ON m.post_id=p.ID AND m.meta_key='_anst_delta' WHERE p.post_type='anst_capitulo'",ARRAY_A);
if(count($rows)!==7)throw new Exception('DELTA_COUNT_CHANGED');
foreach($rows as $r){
 $text=(string)get_field('field_anst07_chapter_delta_json_v1',(int)$r['ID'],false);
 if(hash('sha256',$text)!==hash('sha256',(string)$r['meta_value']))throw new Exception('QUILL_CONTENT_DIFF');
}
$owners=array_map('intval',$wpdb->get_col("SELECT DISTINCT post_author FROM {$wpdb->posts} WHERE post_type='anst_projeto' AND post_status='publish'"));
if(count($owners)!==2)throw new Exception('OWNER_COUNT_CHANGED');
add_filter('anthares_estudio_paid_access',static fn($value,$uid)=>$value||in_array((int)$uid,$owners,true),10,2);
foreach($owners as $uid){
 wp_set_current_user($uid);
 $left=rest_do_request(new WP_REST_Request('GET','/anthares-estudio/v1/bootstrap'));
 $right=rest_do_request(new WP_REST_Request('GET','/anthares-studio/v1/bootstrap'));
 if($left->get_status()!==200||$right->get_status()!==200)throw new Exception('OWNER_GET_FAILED');
 $a=$left->get_data();$b=$right->get_data();
 foreach(['projects','notes','chapters','cards'] as $kind)
  if(count($a[$kind]??[])!==count($b[$kind]??[]))throw new Exception('DATA_PARITY_'.$kind);
 $req=new WP_REST_Request('POST','/anthares-studio/v1/projects');
 $req->set_param('mode','assunto');
 $denied=rest_do_request($req);
 if($denied->get_status()!==423)throw new Exception('WRITE_GATE_FAILED');
}
$zooms=0;
$projects=$wpdb->get_results("SELECT ID,post_author FROM {$wpdb->posts} WHERE post_type='anst_projeto'",ARRAY_A);
foreach($projects as $p){
 $key='_anst_board_zoom_'.$p['ID'];$uid=(int)$p['post_author'];
 if(!metadata_exists('user',$uid,$key))continue;
 if((int)get_user_meta($uid,$key,true)!==(int)anst_user_meta_get($uid,$key,true))throw new Exception('ZOOM_PARITY_FAILED');
 $zooms++;
}
if($zooms!==5)throw new Exception('ZOOM_COUNT_CHANGED');
echo "STUDIO_RUNTIME_LIVE_GET_PARITY=PASS\n";
echo "STUDIO_RUNTIME_OWNER_READS=2 QUILL=7 ZOOMS=5\n";
echo "STUDIO_RUNTIME_POST_STILL_423=1\n";'''
 p=php_cli(script)
 require('STUDIO_RUNTIME_LIVE_GET_PARITY=PASS' in p and 'STUDIO_RUNTIME_POST_STILL_423=1' in p,'LIVE_ACF_PARITY_FAILED')
 for line in p.splitlines():
  if line.startswith('STUDIO_RUNTIME_'):print(line,flush=True)
def atomic(path,bytes):
 fd,name=tempfile.mkstemp(prefix='.anst-runtime-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'wb') as f:f.write(bytes);f.flush();os.fsync(f.fileno())
  os.chmod(name,0o644)
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
require(MODE in ('preflight','enable','verify'),'INVALID_RUNTIME_MODE')
require(php.is_file() and not php.is_symlink() and private.is_dir() and manifest.is_file(),'SITE_PLUGIN_MISSING')
require(hashlib.sha256(legacy.read_bytes()).hexdigest()==ORIGINAL_SHA,'LEGACY_PLUGIN_CHANGED')
require(gitblob(manifest.read_bytes())==MAP_BLOB,'ACF_MAP_CHANGED')
require(len(list((plug/'acf-json').glob('group_anst*.json')))==12,'ACF_GROUPS_CHANGED')
before=php.read_bytes()
marker=b"if (!defined('ABSPATH')) { exit; }"
approval=b"// A ativa\\xc3\\xa7\\xc3\\xa3o do reposit\\xc3\\xb3rio ACF exige tamb\\xc3\\xa9m anst_acf_runtime_enabled=1; OFF mant\\xc3\\xa9m o legado.\\nif (!defined('ANST_ACF_RUNTIME_APPROVED')) { define('ANST_ACF_RUNTIME_APPROVED', true); }"
# Build the exact source diff from the GitHub PR314; only this two-line addition is permitted.
require(before.count(marker)==1 or gitblob(before)==AFTER_BLOB,'LIVE_PLUGIN_MOVED')
expected=before.replace(marker,marker+b'\n'+approval,1) if gitblob(before)==BEFORE_BLOB else before
if gitblob(before)==BEFORE_BLOB:
 require(gitblob(expected)==AFTER_BLOB,'APPROVAL_GIT_BLOB_MISMATCH')
else:
 require(gitblob(before)==AFTER_BLOB,'UNEXPECTED_LIVE_PHP_BLOB')
if MODE=='preflight':
 state(require_on=False)
 check=subprocess.run([cli,'-l'],input=expected,text=False,capture_output=True,timeout=15)
 require(check.returncode==0,'PHP_SYNTAX_FAILED')
 print('STUDIO_RUNTIME_PATCH_PREFLIGHT=PASS',flush=True)
 print('STUDIO_RUNTIME_APPROVED_BLOB='+gitblob(expected),flush=True)
elif MODE=='enable':
 state(require_on=False)
 if gitblob(before)==AFTER_BLOB:
  raise RuntimeError('ALREADY_APPROVED_BUT_RUNTIME_OFF_MANUAL_REVIEW')
 snap=private/('studio-g5-acf-runtime-rollback-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
 require(not snap.exists(),'SNAPSHOT_NAME_COLLISION')
 snap.mkdir(mode=0o700)
 dest=snap/'anthares-estudio.php'
 with open(dest,'xb') as f:f.write(before);f.flush();os.fsync(f.fileno())
 os.chmod(dest,0o600)
 require(dest.read_bytes()==before,'SNAPSHOT_NOT_INTACT')
 touched=False;option=False
 try:
  atomic(php,expected);touched=True
  require(gitblob(php.read_bytes())==AFTER_BLOB,'PHP_PATCH_COPY_FAILED')
  lint=subprocess.run([cli,'-l',str(php)],capture_output=True,text=True,timeout=15)
  require(lint.returncode==0,'PHP_LINT_FAILED')
  state(require_on=False)
  option_update('1');option=True
  state(require_on=True)
  full_read_parity()
  require(hashlib.sha256(legacy.read_bytes()).hexdigest()==ORIGINAL_SHA,'LEGACY_CHANGED_AFTER_ACF')
  print('STUDIO_RUNTIME_ACF_ENABLED_PROVEN=1',flush=True)
  print('STUDIO_RUNTIME_BACKUP_NAME='+snap.name,flush=True)
  print('STUDIO_RUNTIME_WRITES_OFF=1',flush=True)
 except Exception as error:
  failures=[]
  if option:
   try:option_update('0')
   except:failures.append('OPTION')
  if touched:
   try:atomic(php,dest.read_bytes())
   except:failures.append('PHP')
  print('STUDIO_RUNTIME_ENABLE_FAILED='+type(error).__name__+':'+str(error),flush=True)
  try:state(require_on=False)
  except:failures.append('POST_ROLLBACK_STATE')
  print('STUDIO_RUNTIME_AUTO_ROLLBACK='+('FAILED' if failures else 'PASS'),flush=True)
  require(not failures,'RUNTIME_ROLLBACK_NOT_CLEAN')
  raise
elif MODE=='verify':
 require(gitblob(before)==AFTER_BLOB,'LIVE_ACF_APPROVAL_MISSING')
 state(require_on=True)
 full_read_parity()
 print('STUDIO_RUNTIME_READONLY_VERIFY_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 mode=os.getenv('STUDIO_RUNTIME_MODE','preflight')
 if mode not in ('preflight','enable','verify'):raise RuntimeError('INVALID_MODE')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-runtime-') as temp:
  k=pathlib.Path(temp)/'key';k.write_text(key);k.chmod(0o600)
  h=pathlib.Path(temp)/'hosts';h.write_text('anthares-g5-runtime '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-runtime','-o','ConnectTimeout=12',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  result=subprocess.run(cmd,input=REMOTE.replace('MODE_FIELD',mode),text=True,capture_output=True,timeout=190)
  for line in result.stdout.splitlines():
   if line.startswith('STUDIO_RUNTIME_'):print(line,flush=True)
  if result.returncode:
   last=(result.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('STUDIO_RUNTIME_REMOTE_ERROR='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in last)[:130],flush=True)
   raise RuntimeError('STUDIO_RUNTIME_OPERATION_FAILED')
  signal={'preflight':'STUDIO_RUNTIME_PATCH_PREFLIGHT=PASS','enable':'STUDIO_RUNTIME_ACF_ENABLED_PROVEN=1','verify':'STUDIO_RUNTIME_READONLY_VERIFY_PROVEN=1'}[mode]
  if signal not in result.stdout:raise RuntimeError('RUNTIME_PROOF_NOT_RETURNED')
if __name__=='__main__':
 main()
