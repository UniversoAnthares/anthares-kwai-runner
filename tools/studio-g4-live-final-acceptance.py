#!/usr/bin/env python3
"""G4 deployed-runtime acceptance (READ ONLY): private WordPress page, ACF, ownership, flags and cache protections."""
import importlib.util,os,pathlib,subprocess,tempfile
path=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('bridge_g4',path/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(sp);sp.loader.exec_module(bridge)
REMOTE=r"""
import hashlib,json,pathlib,subprocess
home=pathlib.Path.home()
web=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
plugin=web/'wp-content/plugins/anthares-studio'
old=web/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
expected={
'anthares-estudio.php':'8a9becf2da9da692bfecaa508591f9fb33f30780',
'assets/estudio.js':'18669c8fa7f24efcacc9c040145ecc0c7fa4db03',
'acf-json/group_anst02_v1.json':'e52490e072f6cb14e8f270f62962e178e39c8e77',
'docs/acf-core-migration-map.json':'e4eed3976171510c2d4146eee04c38ed6ae2fc4f',
'includes/acf/class-anst-acf-repository.php':'52075b6d0ce8906058ea24579c190a305e2f7ce6',
'includes/acf/class-anst-acf-migrator.php':'286697cc7f2f9afcbcafcd8a52147aa9273f8602'
}
def need(ok,label):
 if not ok:raise RuntimeError(label)
def blob(path):
 d=path.read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
need(plugin.is_dir() and old.is_file() and private.is_dir(),'G4_SITE_EXPECTED_PATHS_MISSING')
need(hashlib.sha256(old.read_bytes()).hexdigest()=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','G4_ORIGINAL_PHP_CHANGED')
for rel,v in expected.items():
 p=plugin/rel
 need(p.is_file() and not p.is_symlink() and blob(p)==v,'G4_RELEASE_BLOB_MISMATCH_'+rel.replace('/','_'))
print('G4_LIVE_SIX_BLOBS=PASS',flush=True)
backup=private/'studio-g4-final-backup-20261117T143339Z'
need((backup/'release-manifest.json').is_file(),'G4_ROLLBACK_MANIFEST_MISSING')
manifest=json.loads((backup/'release-manifest.json').read_text())
need(set(expected)==set(manifest) and all(manifest[k]['after']==v for k,v in expected.items()),'G4_BACKUP_MANIFEST_MISMATCH')
print('G4_LIVE_ROLLBACK_BACKUP=PASS',flush=True)
php=r'''
global $wpdb;
$types=function($prefix)use($wpdb){return $wpdb->get_results("SELECT ID,post_author,post_status FROM {$wpdb->posts} WHERE post_type IN ('{$prefix}_projeto','{$prefix}_nota','{$prefix}_capitulo','{$prefix}_cartao') ORDER BY ID",ARRAY_A);};
$old=$types('aest');$new=$types('anst');
function v($test,$code){if(!$test)WP_CLI::error($code);}
v(count($old)===71&&count($new)===71,'G4_RECORD_COUNTS_CHANGED');
$statuses=function($rows){$counts=['publish'=>0,'trash'=>0];foreach($rows as $p){if(isset($counts[$p['post_status']]))$counts[$p['post_status']]++;}return $counts;};
v($statuses($old)===$statuses($new),'G4_RECORD_STATUSES_CHANGED');
v($statuses($new)['publish']===40&&$statuses($new)['trash']===31,'G4_PUBLISHED_TRASH_CHANGED');
v(anst_acf_runtime_enabled(),'G4_ACF_RUNTIME_OFF');
v((string)get_option('anst_writes_enabled','0')==='0','G4_WRITE_GATE_CHANGED');
v((string)get_option('anst_trash_cleanup_enabled','0')==='0','G4_TRASH_CLEANUP_CHANGED');
v(function_exists('acf_get_local_field_groups'),'G4_ACF_PLUGIN_MISSING');
$groups=0;foreach(acf_get_local_field_groups() as $g){if(str_starts_with((string)($g['key']??''),'group_anst'))$groups++;}
v($groups===12,'G4_ACF_GROUPS_NOT_12');
$map=anst_acf_field_map();
v(isset($map['anst_projeto']['_anst_events']),'G4_ACF_EVENTS_MAPPING_MISSING');
$studio=get_page_by_path('studio',OBJECT,'page');
$estudio=get_page_by_path('estudio',OBJECT,'page');
v($studio instanceof WP_Post&&$studio->post_status==='private','G4_STUDIO_PAGE_NOT_PRIVATE');
v($estudio instanceof WP_Post,'G4_LEGACY_PAGE_MISSING');
v(str_contains($studio->post_content,'[anthares_studio]'),'G4_STUDIO_SHORTCODE_MISSING');
v(str_contains($estudio->post_content,'[anthares_estudio]'),'G4_ORIGINAL_SHORTCODE_MISSING');
$owners=$wpdb->get_col("SELECT DISTINCT post_author FROM {$wpdb->posts} WHERE post_type='anst_projeto' AND post_status='publish' ORDER BY post_author");
v(count($owners)===2,'G4_OWNER_COUNT_CHANGED');
$tested=0;
foreach($owners as $owner){
 wp_set_current_user((int)$owner);
 $out=anst_bootstrap(true);
 v($out instanceof WP_REST_Response,'G4_INLINE_BOOTSTRAP_INVALID');
 $data=$out->get_data();
 v(isset($data['slim'])&&$data['slim']===true&&isset($data['projects']),'G4_BOOTSTRAP_SHAPE_INVALID');
 foreach($data['projects'] as $row)v((int)get_post((int)$row['id'])->post_author===(int)$owner,'G4_OWNER_PROJECT_LEAK');
 if(!anst_can_use())continue;
 $html=do_shortcode('[anthares_studio]');
 v(str_contains($html,'id="anthares-estudio-root"'),'G4_PRIVATE_SHORTCODE_RUNTIME_FAILED');
 v(is_array(anst_lesson_settings()),'G4_ACF_LESSON_OPTION_FAILURE');
 $get=new WP_REST_Request('GET','/anthares-studio/v1/bootstrap');
 v(anst_permission($get)===true,'G4_OWNER_GET_PERMISSION_FAILED');
 $post=new WP_REST_Request('POST','/anthares-studio/v1/projects');
 $blocked=anst_permission($post);
 v(is_wp_error($blocked)&&$blocked->get_error_data()['status']===423,'G4_WRITE_GATE_NOT_ENFORCED');
 $tested++;
}
v($tested>=1,'G4_NO_AUTHORIZED_OWNER_TO_TEST');
wp_set_current_user(0);
$blocked=anst_permission(new WP_REST_Request('GET','/anthares-studio/v1/bootstrap'));
v($blocked===false,'G4_ANONYMOUS_PERMISSION_EXPOSED');
// Simulate a page query for WordPress's template_redirect. No real user browser tokens are accessed.
wp_set_current_user((int)$owners[0]);
global $wp_query,$post;
$wp_query=new WP_Query(['page_id'=>(int)$studio->ID,'post_type'=>'page','post_status'=>'private']);
$post=$studio;
$wp_query->is_page=true;
do_action('template_redirect');
v(defined('DONOTCACHEPAGE') && DONOTCACHEPAGE,'G4_PRIVATE_PAGE_CACHE_NOT_DISABLED');
WP_CLI::line('G4_LIVE_71_71_AND_40_31=PASS');
WP_CLI::line('G4_LIVE_ACF_12_GROUPS_AND_EVENTS=PASS');
WP_CLI::line('G4_LIVE_PRIVATE_PAGE_SHORTCODE=PASS');
WP_CLI::line('G4_LIVE_OWNER_AUTHORIZATION=PASS');
WP_CLI::line('G4_LIVE_WRITE_GATE_423=PASS');
WP_CLI::line('G4_LIVE_PRIVATE_CACHE_GUARD=PASS');
WP_CLI::line('G4_LIVE_ACCEPTANCE_PASS=1');
'''
cmd=['/opt/alt/php83/usr/bin/php','/usr/local/bin/wp','--path='+str(web),'--skip-themes','eval',php]
r=subprocess.run(cmd,text=True,capture_output=True,timeout=120)
for line in r.stdout.splitlines():
 if line.startswith('G4_'):print(line,flush=True)
if r.returncode:
 last=(r.stderr.strip().splitlines() or ['NO_STDERR'])[-1]
 print('G4_LIVE_ERROR='+''.join(c if c.isalnum() or c in ' _:=/-.' else '_' for c in last)[:175],flush=True)
need(r.returncode==0 and 'G4_LIVE_ACCEPTANCE_PASS=1' in r.stdout,'G4_LIVE_VERIFY_FAILED')
print('G4_G4_HOSTINGER_READONLY_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('BRANCH_WRONG')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g4-live-final-') as tmp:
  d=pathlib.Path(tmp);keyfile=d/'key';keyfile.write_text(key);keyfile.chmod(0o600)
  hosts=d/'hosts';hosts.write_text('anthares-g4-live-final '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(keyfile),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(hosts),
       '-o','HostKeyAlias=anthares-g4-live-final','-o','ConnectTimeout=12',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=165)
  for line in r.stdout.splitlines():
   if line.startswith('G4_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G4_LIVE_REMOTE_ERROR='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in last)[:140],flush=True)
   raise RuntimeError('G4_LIVE_QA_REMOTE_FAILED')
  if 'G4_G4_HOSTINGER_READONLY_PROVEN=1' not in r.stdout:raise RuntimeError('G4_PROOF_MISSING')
if __name__=='__main__':main()
