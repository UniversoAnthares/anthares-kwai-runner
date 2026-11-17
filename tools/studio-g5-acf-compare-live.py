#!/usr/bin/env python3
"""Read-only full G5 post/user/options ACF content and reference comparison on production."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('g5_bridge',here/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(sp);sp.loader.exec_module(bridge)
REMOTE=r"""
import hashlib,pathlib,subprocess,re
home=pathlib.Path.home();web=home/'domains/anthares.us/public_html'
plugin=web/'wp-content/plugins/anthares-studio'
manifest=plugin/'docs/acf-core-migration-map.json'
loader=plugin/'includes/acf/class-anst-acf-migrator.php'
def check(b,code):
 if not b:raise RuntimeError(code)
def blob(p):
 d=p.read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
check(blob(plugin/'anthares-estudio.php')=='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb','PLUGIN_VERSION_CHANGED')
check(blob(manifest)=='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325','MANIFEST_CHANGED')
PHP=r'''
$cls=new ANST_ACF_Migrator();
$ref=new ReflectionClass($cls);
$source=$ref->getMethod('current_source')->invoke($cls);
$expected=$ref->getMethod('expected_items')->invoke($cls,$source['posts']);
if (count($source['posts'])!==71 || count($expected['items'])!==412 ||
    count($expected['zooms'])!==1 || $expected['reference_errors']!==0 ||
    !hash_equals('bced1ad06c27a43a25585d9663457dd2cdc2f4c58f24bb1dada8696defe10bd1',$source['fingerprint'])) {
    WP_CLI::error('G5_SOURCE_CHANGED_DURING_VERIFY');
}
$mismatches=0;$checked=0;$deltas=0;
foreach ($expected['items'] as $e) {
    $id=(int)$e['post'];
    $exists=metadata_exists('post',$id,$e['name']);
    $actual=$exists?(string)get_post_meta($id,$e['name'],true):'';
    $reference=(string)get_post_meta($id,'_'.$e['name'],true);
    if (!$exists || $reference!==$e['key'] ||
        !hash_equals(hash('sha256',$e['raw']),hash('sha256',$actual)))$mismatches++;
    if ($e['name']==='studio_chapter_delta_json') {
        $deltas++;
        if (!is_array(json_decode($e['raw'],true)))$mismatches++;
    }
    $checked++;
}
foreach ($expected['zooms'] as $uid=>$json) {
    $exists=metadata_exists('user',(int)$uid,'studio_user_board_zoom_index_json');
    $val=$exists?(string)get_user_meta((int)$uid,'studio_user_board_zoom_index_json',true):'';
    $key=(string)get_user_meta((int)$uid,'_studio_user_board_zoom_index_json',true);
    if (!$exists || $key!=='field_anst16u_user_board_zoom_index_json_v1' ||
        !hash_equals(hash('sha256',$json),hash('sha256',$val)))$mismatches++;
    $checked++;
}
$actual=get_option('options_studio_course_lesson_links_json',null);
$key=(string)get_option('_options_studio_course_lesson_links_json','');
if (!is_string($actual)||$key!=='field_anst16c_course_lesson_links_json_v1' ||
    !hash_equals(hash('sha256',$expected['course']),hash('sha256',(string)$actual)))$mismatches++;
$checked++;
if ($checked!==414 || $deltas!==7 || $mismatches)WP_CLI::error('G5_ACF_VALUE_MISMATCH');
WP_CLI::line('G5_COMPARE_SOURCE_FINGERPRINT='.$source['fingerprint']);
WP_CLI::line('G5_COMPARE_POSTMETA='.$checked-2);
WP_CLI::line('G5_COMPARE_USERZOOM=1');
WP_CLI::line('G5_COMPARE_COURSE=1');
WP_CLI::line('G5_COMPARE_DELTAS='.$deltas);
WP_CLI::line('G5_COMPARE_MISMATCHES='.$mismatches);
WP_CLI::success('G5_414_ACF_VALUES_MATCH');
'''
args=['/opt/alt/php83/usr/bin/php','/usr/local/bin/wp','--path='+str(web),'--skip-themes',
      '--require='+str(loader),'eval',PHP]
p=subprocess.run(args,text=True,capture_output=True,timeout=100)
for line in p.stdout.splitlines():
 if line.startswith('G5_'):print(line,flush=True)
if p.returncode:
 last=(p.stderr.strip().splitlines() or ['NO_STDERR'])[-1]
 safe=''.join(c if c.isalnum() or c in ' _.:/-' else '_' for c in last)[:120]
 print('G5_COMPARE_ERROR='+safe,flush=True)
check(p.returncode==0 and 'G5_414_ACF_VALUES_MATCH' in p.stdout+p.stderr,'G5_COMPARE_FAILED')
print('G5_READONLY_ACF_MATCH_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-compare-') as tmp:
  p=pathlib.Path(tmp);k=p/'key';k.write_text(key);k.chmod(0o600)
  h=p/'hosts';h.write_text('anthares-g5-compare '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes',
       '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-compare','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=130)
  for line in r.stdout.splitlines():
   if line.startswith('G5_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G5_COMPARE_REMOTE_ERROR='+''.join(x if x.isalnum() or x in ' _:.-' else '_' for x in last)[:120],flush=True)
   raise RuntimeError('G5_COMPARE_REMOTE_FAILED')
  if 'G5_READONLY_ACF_MATCH_PROVEN=1' not in r.stdout:raise RuntimeError('G5_COMPARE_PROOF_MISSING')
if __name__=='__main__':main()
