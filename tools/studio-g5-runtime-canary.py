#!/usr/bin/env python3
"""Production read-only ACF runtime canary: forced ON in CLI memory, no persisted option."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g5_bridge',here/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import hashlib,pathlib,subprocess,re
home=pathlib.Path.home()
web=home/'domains/anthares.us/public_html'
plugin=web/'wp-content/plugins/anthares-studio'
def chk(ok,label):
 if not ok:raise RuntimeError(label)
data=(plugin/'docs/acf-core-migration-map.json').read_bytes()
blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
chk(blob=='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325','G5_MANIFEST_CHANGED')
PHP=r'''
global $wpdb;
if ((string)get_option('anst_acf_runtime_enabled','0')!=='0') WP_CLI::error('CANARY_EXPECTS_RUNTIME_OFF');
if (!function_exists('acf_add_local_field_group'))WP_CLI::error('ACF_NOT_AVAILABLE');
$users=$wpdb->get_col("SELECT DISTINCT post_author FROM {$wpdb->posts} WHERE post_type IN ('anst_projeto','anst_nota','anst_capitulo','anst_cartao') ORDER BY post_author");
if (!$users)WP_CLI::error('G5_NO_OWNERS');
$baseline=[];
foreach ($users as $user) {
    wp_set_current_user((int)$user);
    $r=anst_bootstrap(new WP_REST_Request('GET','/anthares-studio/v1/bootstrap'));
    if (is_wp_error($r))WP_CLI::error('G5_BOOTSTRAP_LEGACY_ERROR');
    $raw=wp_json_encode($r->get_data(),JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
    if (!is_string($raw))WP_CLI::error('G5_LEGACY_RESPONSE_INVALID');
    $baseline[(int)$user]=hash('sha256',$raw);
}
add_filter('pre_option_anst_acf_runtime_enabled',static fn($value)=>'1',999);
foreach (glob(WP_PLUGIN_DIR.'/anthares-studio/acf-json/group_anst*.json')?:[] as $path) {
    $g=json_decode((string)file_get_contents($path),true);
    if (!is_array($g)||($g['active']??true)!==false)WP_CLI::error('G5_LOCAL_GROUP_INVALID');
    $g['active']=true;
    acf_add_local_field_group($g);
}
$fn=(new ReflectionFunction('anst_bootstrap'))->getFileName();
$main=WP_PLUGIN_DIR.'/anthares-studio/anthares-estudio.php';
WP_CLI::line('G5_CANARY_BOOTSTRAP_FROM_MAIN='.(realpath($fn)===realpath($main)?'1':'0'));
WP_CLI::line('G5_CANARY_MAIN_INCLUDED='.(in_array(realpath($main),array_map('realpath',get_included_files()),true)?'1':'0'));
WP_CLI::line('G5_CANARY_MAIN_HAS_ACF_CONST='.(str_contains((string)file_get_contents($main),'ANST_ACF_RUNTIME_APPROVED')?'1':'0'));
WP_CLI::line('G5_CANARY_PLUGIN_MAIN_SHA256='.hash_file('sha256',$main));
WP_CLI::line('G5_CANARY_APPROVED_CONST='.(defined('ANST_ACF_RUNTIME_APPROVED')?(ANST_ACF_RUNTIME_APPROVED?'1':'0'):'UNDEFINED'));
WP_CLI::line('G5_CANARY_OPTION_READ='.get_option('anst_acf_runtime_enabled','0'));
WP_CLI::line('G5_CANARY_ADAPTER_ENABLED='.(anst_acf_runtime_enabled()?'1':'0'));
if (!anst_acf_runtime_enabled())WP_CLI::error('G5_CANARY_NOT_ENABLED');
if (count(acf_get_local_field_groups())<12)WP_CLI::error('G5_ACF_GROUP_REGISTRATION_FAILED');
$bad=0;$tested=0;$delta=0;
$map=anst_acf_field_map();
foreach ($map as $postType=>$fields) {
    $posts=$wpdb->get_col($wpdb->prepare("SELECT ID FROM {$wpdb->posts} WHERE post_type=%s ORDER BY ID",$postType));
    foreach ($posts as $id) {
        foreach ($fields as $legacyKey=>$target) {
            if (!metadata_exists('post',(int)$id,$legacyKey)) continue;
            $orig=(string)get_post_meta((int)$id,$legacyKey,true);
            $read=anst_meta_get((int)$id,$legacyKey,true);
            if (!hash_equals(hash('sha256',$orig),hash('sha256',(string)$read)))$bad++;
            if ($target['name']==='studio_chapter_delta_json')$delta++;
            $tested++;
        }
    }
}
if ($tested!==412||$delta!==7)WP_CLI::error('G5_CANARY_FIELD_COUNTS_CHANGED');
foreach ($users as $user) {
    wp_set_current_user((int)$user);
    $r=anst_bootstrap(new WP_REST_Request('GET','/anthares-studio/v1/bootstrap'));
    if (is_wp_error($r)) WP_CLI::error('G5_ACF_BOOTSTRAP_ERROR');
    $raw=wp_json_encode($r->get_data(),JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES);
    if (!is_string($raw)||!hash_equals($baseline[(int)$user],hash('sha256',$raw)))$bad++;
}
$lesson=anst_acf_lesson_option_get();
if ($lesson!==get_option('anst_section_lesson_videos',[]))$bad++;
if ($bad)WP_CLI::error('G5_ACF_CANARY_CONTENT_DIFFERENCE count='.$bad);
WP_CLI::line('G5_CANARY_POSTMETA_MATCH='.$tested);
WP_CLI::line('G5_CANARY_QUILL_MATCH='.$delta);
WP_CLI::line('G5_CANARY_OWNERS_COMPARE='.count($users));
WP_CLI::line('G5_CANARY_ACF_GROUPS=12');
WP_CLI::line('G5_CANARY_MISMATCHES=0');
WP_CLI::success('G5_ACF_READ_PATH_CANARY_PASS');
'''
cmd=['/opt/alt/php83/usr/bin/php','/usr/local/bin/wp','--path='+str(web),'--skip-themes','eval',PHP]
r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
for line in r.stdout.splitlines():
 if line.startswith('G5_CANARY_'):print(line,flush=True)
if r.returncode:
 last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
 safe=''.join(c if c.isalnum() or c in ' _:=./-' else '_' for c in last)[:160]
 print('G5_CANARY_ERROR_LAST='+safe,flush=True)
chk(r.returncode==0 and 'G5_ACF_READ_PATH_CANARY_PASS' in r.stdout+r.stderr,'G5_ACF_CANARY_FAILED')
print('G5_ACF_READ_PATH_CANARY_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-canary-') as tmp:
  p=pathlib.Path(tmp);k=p/'key';k.write_text(key);k.chmod(0o600)
  h=p/'hosts';h.write_text('anthares-g5-canary '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-canary','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=160)
  for line in r.stdout.splitlines():
   if line.startswith('G5_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G5_CANARY_REMOTE_ERROR='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in last)[:120],flush=True)
   raise RuntimeError('G5_CANARY_REMOTE_FAILED')
  if 'G5_ACF_READ_PATH_CANARY_PROVEN=1' not in r.stdout:raise RuntimeError('G5_CANARY_PROOF_MISSING')
if __name__=='__main__':main()
