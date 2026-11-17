#!/usr/bin/env python3
"""Read-only G5 ACF runtime parity against live data, enabling ACF only inside isolated PHP CLI."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('anthares_g5_bridge',here/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import hashlib,json,os,pathlib,re,subprocess,sys
home=pathlib.Path.home()
site=home/'domains/anthares.us/public_html'
new=site/'wp-content/plugins/anthares-studio'
legacy=site/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
def require(cond,code):
 if not cond:raise RuntimeError(code)
def gitblob(b):
 return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
require(gitblob((new/'anthares-estudio.php').read_bytes())=='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb','G5_LIVE_PLUGIN_CHANGED')
require(gitblob((new/'docs/acf-core-migration-map.json').read_bytes())=='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325','G5_MAP_CHANGED')
require(hashlib.sha256(legacy.read_bytes()).hexdigest()=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_CHANGED')
php=r'''
define('WP_USE_THEMES',false);
define('DISABLE_WP_CRON',true);
require 'WPLOAD_HERE';
if(!function_exists('anst_acf_runtime_enabled') || !function_exists('acf_add_local_field_group'))throw new Exception('ACF_PLUGIN_NOT_LOADED');
if((string)get_option('anst_acf_runtime_enabled','0')!=='0')throw new Exception('ACF_FLAG_UNEXPECTED');
if((string)get_option('anst_writes_enabled','0')!=='0')throw new Exception('WRITE_GATE_UNEXPECTED');
if((string)get_option('anst_trash_cleanup_enabled','0')!=='0')throw new Exception('TRASH_GATE_UNEXPECTED');
define('ANST_ACF_RUNTIME_APPROVED',true);
add_filter('pre_option_anst_acf_runtime_enabled',static fn()=>'1');
if(!anst_acf_runtime_enabled())throw new Exception('ACF_PREVIEW_NOT_ENABLED');
$groups=glob('GROUPS_HERE')?:[];
if(count($groups)!==12)throw new Exception('GROUP_COUNT_CHANGED');
foreach($groups as $path){
 $g=json_decode((string)file_get_contents($path),true);
 if(!is_array($g)||($g['active']??true)!==false)throw new Exception('GROUP_INVALID');
 $g['active']=true;acf_add_local_field_group($g);
}
foreach(['field_anst01_start_mode_v1','field_anst07_chapter_delta_json_v1','field_anst16c_course_lesson_links_json_v1'] as $field){
 if(!acf_get_field($field))throw new Exception('ACF_KEY_UNREGISTERED');
}
$source=(array)get_option('anst_section_lesson_videos',[]);
$course=anst_acf_lesson_option_get();
if($source!==$course)throw new Exception('COURSE_OPTIONS_DIFFERENT');
global $wpdb;
$rows=$wpdb->get_results("SELECT p.ID,m.meta_value FROM {$wpdb->posts} p JOIN {$wpdb->postmeta} m ON m.post_id=p.ID AND m.meta_key='_anst_delta' WHERE p.post_type='anst_capitulo' ORDER BY p.ID",ARRAY_A);
if(count($rows)!==7)throw new Exception('DELTA_COUNT_CHANGED');
foreach($rows as $row) {
 $delta=(string)get_field('field_anst07_chapter_delta_json_v1',(int)$row['ID'],false);
 if(!hash_equals(hash('sha256',(string)$row['meta_value']),hash('sha256',$delta)))throw new Exception('DELTA_ACF_MISMATCH');
}
$owners=array_map('intval',$wpdb->get_col("SELECT DISTINCT post_author FROM {$wpdb->posts} WHERE post_type='anst_projeto' AND post_status='publish'"));
if(count($owners)<2)throw new Exception('OWNERS_UNEXPECTED');
add_filter('anthares_estudio_paid_access',static fn($value,$user)=>$value||in_array((int)$user,$owners,true),10,2);
$counts=[];$types=['projects','notes','chapters','cards'];
foreach($owners as $user) {
 wp_set_current_user($user);
 $a=rest_do_request(new WP_REST_Request('GET','/anthares-estudio/v1/bootstrap'));
 $b=rest_do_request(new WP_REST_Request('GET','/anthares-studio/v1/bootstrap'));
 if($a->get_status()!==200 || $b->get_status()!==200)throw new Exception('READ_API_STATUS_FAIL');
 $left=$a->get_data();$right=$b->get_data();
 foreach($types as $type){
  if(!isset($left[$type],$right[$type])||count($left[$type])!==count($right[$type]))
   throw new Exception('READ_TYPE_COUNT_MISMATCH_'.$type);
  $counts[$type]=($counts[$type]??0)+count($left[$type]);
 }
}
$zooms=0;
$projects=$wpdb->get_results("SELECT ID,post_author FROM {$wpdb->posts} WHERE post_type='anst_projeto'",ARRAY_A);
foreach($projects as $row){
 $pid=(int)$row['ID'];$uid=(int)$row['post_author'];$key='_anst_board_zoom_'.$pid;
 if(!metadata_exists('user',$uid,$key))continue;
 if((int)get_user_meta($uid,$key,true)!==(int)anst_user_meta_get($uid,$key,true))
  throw new Exception('ACF_ZOOM_MISMATCH');
 $zooms++;
}
if($zooms!==5)throw new Exception('ACF_ZOOM_COUNT_MISMATCH');
if((string)get_option('anst_acf_runtime_enabled','0')!=='0')throw new Exception('OPTION_WAS_MODIFIED');
if((string)get_option('anst_writes_enabled','0')!=='0')throw new Exception('WRITE_FLAG_WAS_MODIFIED');
$posts=(int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('anst_projeto','anst_nota','anst_capitulo','anst_cartao')");
if($posts!==71)throw new Exception('POSTS_CHANGED');
echo "STUDIO_G5_ACF_IN_MEMORY_READ_PASS=1\n";
echo "STUDIO_G5_ACF_API_OWNERS=".count($owners)."\n";
echo "STUDIO_G5_ACF_DELTA_PARITY=7\n";
echo "STUDIO_G5_ACF_ZOOM_PARITY=".$zooms."\n";
echo "STUDIO_G5_ACF_SOURCE_POSTS=71\n";
echo "STUDIO_G5_ACF_WEB_OPTION_OFF=1\n";
'''
php=php.replace('WPLOAD_HERE',str(site/'wp-load.php')).replace('GROUPS_HERE',str(new/'acf-json/group_anst*.json'))
p=subprocess.run(['/opt/alt/php83/usr/bin/php','-d','display_errors=stderr','-r',php],capture_output=True,text=True,timeout=90)
for line in p.stdout.splitlines():
 if line.startswith('STUDIO_G5_'):print(line,flush=True)
if p.returncode:
 err=p.stderr
 kind='READ_RUNTIME_FAILURE'
 for pat,reason in [('ACF_PLUGIN_NOT_LOADED','ACF_PLUGIN_NOT_LOADED'),('GROUP_COUNT_CHANGED','GROUP_COUNT_CHANGED'),('ACF_KEY_UNREGISTERED','ACF_KEY_UNREGISTERED'),('READ_API_STATUS_FAIL','READ_API_STATUS_FAIL'),('READ_TYPE_COUNT_MISMATCH','READ_TYPE_COUNT_MISMATCH'),('DELTA_ACF_MISMATCH','DELTA_ACF_MISMATCH'),('ACF_ZOOM_MISMATCH','ACF_ZOOM_MISMATCH'),('COURSE_OPTIONS_DIFFERENT','COURSE_OPTIONS_DIFFERENT'),('OWNERS_UNEXPECTED','OWNERS_UNEXPECTED'),('Fatal error','PHP_FATAL')]:
  if pat in err:kind=reason;break
 print('STUDIO_G5_ACF_READ_ERROR='+kind,flush=True)
 raise RuntimeError('READ_ONLY_G5_PARITY_FAILED')
require('STUDIO_G5_ACF_IN_MEMORY_READ_PASS=1' in p.stdout,'SUCCESS_SIGNAL_ABSENT')
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-readpath-') as temp:
  k=pathlib.Path(temp)/'key';k.write_text(key);k.chmod(0o600)
  h=pathlib.Path(temp)/'hosts';h.write_text('anthares-g5-read '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-read','-o','ConnectTimeout=12',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  p=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=125)
  for line in p.stdout.splitlines():
   if line.startswith('STUDIO_G5_'):print(line,flush=True)
  if p.returncode:
   tail=(p.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('STUDIO_G5_READ_REMOTE_ERROR='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in tail)[:140],flush=True)
   raise RuntimeError('G5_PARITY_REMOTE_FAILED')
  if 'STUDIO_G5_ACF_IN_MEMORY_READ_PASS=1' not in p.stdout:raise RuntimeError('PARITY_NOT_PROVEN')
if __name__=='__main__':
 main()
