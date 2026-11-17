#!/usr/bin/env python3
"""Guarded release of new Studio code only, preserving legacy and all database records.
Uses existing protected SSH bridge, verified private backup, per-file atomic replacement.
Run with MODE=preflight or MODE=deploy. G5 ACF runtime and all writes remain disabled.
"""
import importlib.util,os,pathlib,re,subprocess,tempfile
THIS=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('anthares_g5_bridge',THIS/'studio-g5g6-isolated-qa.py')
bridge_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge_module)

REMOTE=r"""
import datetime,hashlib,json,os,pathlib,shutil,stat,subprocess,sys,tempfile
MODE='MODE_MARKER'
home=pathlib.Path.home()
root=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
live=root/'wp-content/plugins/anthares-studio'
legacy=root/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
source=private/'studio-g6-review-20261116'
phpbin='/opt/alt/php83/usr/bin/php'
SHA_LIVE='042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7'
SHA_LEGACY='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'
SHA_CSS_MAIN='6fc81afb986db6c427da558fd6ed13218575ea90446cbabd0400a9f8e827de97'
SHA_CSS_DARK='2917c1acbfa82098989915b7f1725b729d6345fe920a71398b19f4757563435b'
EXPECTED_HEAD='3efad7ad3b41e765132f625202daad88f8f2ee7d'
EXPECTED_BLOBS={
 'anthares-estudio.php':'0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb',
 'assets/estudio.css':'a0238eb95b78da38b427b1da566463f611fcd37c',
 'assets/estudio-dark.css':'1afedf2d97abcbd8ccdbf78251bcf1f4c68fe6d9'
}
def require(ok,label):
 if not ok:raise RuntimeError(label)
def sha(payload):
 return hashlib.sha256(payload).hexdigest()
def gitblob(payload):
 return hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
def audit_wp():
 code=r'''define("WP_USE_THEMES",false);define("DISABLE_WP_CRON",true);require "WPLOAD_MARKER";
global $wpdb;
$oldTypes="'aest_projeto','aest_nota','aest_capitulo','aest_cartao'";
$newTypes="'anst_projeto','anst_nota','anst_capitulo','anst_cartao'";
$count=function($types,$status="")use($wpdb){
 $sql="SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN (".$types.")";
 if($status!=="")$sql.=$wpdb->prepare(" AND post_status=%s",$status);
 return (int)$wpdb->get_var($sql);
};
$o=['old'=>$count($oldTypes),'new'=>$count($newTypes),
  'old_publish'=>$count($oldTypes,'publish'),'new_publish'=>$count($newTypes,'publish'),
  'old_trash'=>$count($oldTypes,'trash'),'new_trash'=>$count($newTypes,'trash'),
  'writes'=>(string)get_option('anst_writes_enabled','0'),
  'cleanup'=>(string)get_option('anst_trash_cleanup_enabled','0'),
  'acf_runtime'=>(string)get_option('anst_acf_runtime_enabled','0'),
  'studio_private'=>(get_page_by_path('studio',OBJECT,'page')->post_status??'')==='private',
  'studio_active'=>in_array('anthares-studio/anthares-estudio.php',(array)get_option('active_plugins',[]),true),
  'legacy_active'=>in_array('anthares-estudio/anthares-estudio.php',(array)get_option('active_plugins',[]),true)];
echo 'STUDIO_RELEASE_STATE='.wp_json_encode($o)."\n";'''
 code=code.replace('WPLOAD_MARKER',str(root/'wp-load.php'))
 p=subprocess.run([phpbin,'-r',code],capture_output=True,text=True,timeout=55)
 require(p.returncode==0,'WP_BOOTSTRAP_FAILED')
 line=next((x.split('=',1)[1] for x in p.stdout.splitlines() if x.startswith('STUDIO_RELEASE_STATE=')),None)
 require(bool(line),'WP_AUDIT_RETURN_MISSING')
 o=json.loads(line)
 for key in ('old','new'):require(o[key]==71,'DATA_COUNT_CHANGED_'+key)
 for key in ('old_publish','new_publish'):require(o[key]==40,'PUBLISHED_COUNT_CHANGED_'+key)
 for key in ('old_trash','new_trash'):require(o[key]==31,'TRASH_COUNT_CHANGED_'+key)
 for key in ('writes','cleanup','acf_runtime'):require(o[key]=='0','FLAG_NOT_SAFE_'+key)
 require(o['studio_private'] and o['studio_active'] and o['legacy_active'],'WP_VISIBILITY_OR_PLUGIN_STATE_CHANGED')
 return o
def write_atomic(path,data,mode=0o644):
 fd,name=tempfile.mkstemp(prefix='.anst-stage-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chmod(name,mode)
  return pathlib.Path(name)
 except:
  if os.path.exists(name):os.unlink(name)
  raise
def tree_no_symlinks(dir):
 for p in dir.rglob('*'):
  require(not p.is_symlink(),'SOURCE_OR_TARGET_LINK_FORBIDDEN')
def patched_plugin(stage):
 php=stage/'anthares-estudio.php'
 content=php.read_bytes().decode('utf8')
 before="""add_filter('body_class', function($classes){
 if(is_page('studio') && (!is_user_logged_in() || !anst_can_use()))$classes[]='aest-access-gate';
 return $classes;
});"""
 after="""add_filter('body_class', function($classes){
 if (is_page('studio')) {
  // Identidade visual estável e exclusiva do novo Studio.
  $classes[] = 'anst-studio-page';
  if (!is_user_logged_in() || !anst_can_use()) $classes[] = 'aest-access-gate';
 }
 return $classes;
});"""
 require(content.count(before)==1,'G6_BASE_BODY_FILTER_UNEXPECTED')
 content=content.replace(before,after)
 anchor="function anst_trash_cleanup_enabled(){return (string)get_option('anst_trash_cleanup_enabled','0')==='1';}"
 guard="""
/** Preserva itens ANST da lixeira quando WordPress executa limpeza nativa. */
add_filter('pre_delete_post',static function($pre,$post,$force_delete){
 if($pre!==null)return $pre;
 if(!anst_trash_cleanup_enabled()&&doing_action('wp_scheduled_delete')&&
    $post instanceof WP_Post&&in_array($post->post_type,anst_trash_types(),true))return false;
 return $pre;
},10,3);"""
 require(content.count(anchor)==1,'G6_BASE_TRASH_GUARD_CHANGED')
 content=content.replace(anchor,anchor+'\n'+guard)
 php.write_bytes(content.encode('utf8'))
 for name,n in [('estudio.css',509),('estudio-dark.css',216)]:
  p=stage/'assets'/name
  content=p.read_bytes()
  require(content.count(b'page-id-19344')==n,'G6_BASE_SELECTOR_COUNT_MISMATCH')
  content=content.replace(b'page-id-19344',b'anst-studio-page')
  if name=='estudio.css':
   require(content.count(b'article#post-19344')==6,'G6_ARTICLE_COUNT_MISMATCH')
   content=content.replace(b'article#post-19344',b'article')
  p.write_bytes(content)
 for name,digest in EXPECTED_BLOBS.items():
  require(gitblob((stage/name).read_bytes())==digest,'PR314_BLOB_MISMATCH_'+name)
 return stage

require(MODE in ('preflight','deploy'),'INVALID_DEPLOY_MODE')
require(live.is_dir() and not live.is_symlink() and source.is_dir() and private.is_dir(),'EXPECTED_SITE_PATHS_ABSENT')
require(legacy.is_file() and sha(legacy.read_bytes())==SHA_LEGACY,'LEGACY_PHP_CHANGED')
require(sha((live/'anthares-estudio.php').read_bytes())==SHA_LIVE,'LIVE_PHP_BASELINE_CHANGED')
require(sha((live/'assets/estudio.css').read_bytes())==SHA_CSS_MAIN,'LIVE_CSS_BASELINE_CHANGED')
require(sha((live/'assets/estudio-dark.css').read_bytes())==SHA_CSS_DARK,'LIVE_DARK_CSS_BASELINE_CHANGED')
audit_wp()
git=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=8).strip()
require(git==EXPECTED_HEAD,'DEV_HEAD_CHANGED')
tree_no_symlinks(live)
stage_parent=pathlib.Path(tempfile.mkdtemp(prefix='studio-release-stage-',dir=private))
backup=None
try:
 stage=stage_parent/'anthares-studio'
 shutil.copytree(source/'anthares-studio',stage)
 tree_no_symlinks(stage)
 patched_plugin(stage)
 for p in [stage/'anthares-estudio.php',stage/'includes/acf/class-anst-acf-repository.php']:
  lint=subprocess.run([phpbin,'-l',str(p)],capture_output=True,text=True,timeout=20)
  require(lint.returncode==0,'PHP_LINT_FAILED_'+p.name)
 targets=[]
 for p in stage.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(stage)
  if len(rel.parts)==1 and rel.name!='anthares-estudio.php':continue
  if len(rel.parts)>1 and rel.parts[0] not in ('assets','includes','acf-json'):continue
  targets.append(rel)
 require(5<len(targets)<120,'DEPLOY_FILE_SET_UNEXPECTED')
 files_changed=[rel for rel in targets if not (live/rel).is_file() or (live/rel).read_bytes()!=(stage/rel).read_bytes()]
 print('STUDIO_RELEASE_PREFLIGHT_FILES='+str(len(targets)),flush=True)
 print('STUDIO_RELEASE_PREFLIGHT_CHANGES='+str(len(files_changed)),flush=True)
 print('STUDIO_RELEASE_INTEGRATION_BLOBS=PASS',flush=True)
 print('STUDIO_RELEASE_PREVIOUS_71=PASS',flush=True)
 if MODE=='preflight':
  print('STUDIO_RELEASE_PREFLIGHT_PASS=1',flush=True)
 else:
  backup=private/('studio-g4g5-g6-backup-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
  require(not backup.exists(),'BACKUP_NAME_CONFLICT')
  backup.mkdir(mode=0o700)
  archive=backup/'anthares-studio-before'
  shutil.copytree(live,archive)
  tree_no_symlinks(archive)
  for rel in targets:
   if (live/rel).is_file():
    require((archive/rel).is_file() and (archive/rel).read_bytes()==(live/rel).read_bytes(),'BACKUP_INTEGRITY_ERROR')
  file_order=sorted(files_changed,key=lambda rel:(rel.as_posix()=='anthares-estudio.php',rel.as_posix()))
  original_checksums={rel:sha((live/rel).read_bytes()) if (live/rel).is_file() else None for rel in file_order}
  touched=[]
  try:
   for rel in file_order:
    dest=live/rel
    parent=dest.parent
    parent.mkdir(parents=True,exist_ok=True)
    require(parent.resolve().is_relative_to(live.resolve()),'WRITE_PARENT_OUTSIDE_PLUGIN')
    require(not dest.is_symlink(),'TARGET_LINK_FORBIDDEN')
    was=original_checksums[rel]
    require((sha(dest.read_bytes()) if dest.is_file() else None)==was,'CONCURRENT_FILE_CHANGE')
    data=(stage/rel).read_bytes()
    tmp=write_atomic(dest,data,0o644)
    try:os.replace(tmp,dest)
    finally:
     if tmp.exists():tmp.unlink()
    touched.append(rel)
   # Runtime PHP must boot with both plugins and reflect unchanged data/flags.
   lint=subprocess.run([phpbin,'-l',str(live/'anthares-estudio.php')],capture_output=True,text=True,timeout=20)
   require(lint.returncode==0,'LIVE_PHP_LINT_FAILED')
   audit_wp()
   require(sha(legacy.read_bytes())==SHA_LEGACY,'LEGACY_CHANGED_DURING_DEPLOY')
   for name,digest in EXPECTED_BLOBS.items():
    require(gitblob((live/name).read_bytes())==digest,'DEPLOYED_BLOB_CHANGED_'+name)
   require((live/'assets/studio-g6-navigation.css').is_file(),'G6_CSS_ASSET_MISSING')
   require((live/'includes/acf/class-anst-acf-repository.php').is_file(),'ACF_REPO_CLASS_MISSING')
   print('STUDIO_CODE_DEPLOY_PROVEN=1',flush=True)
   print('STUDIO_G6_NAV_ASSET=1 STUDIO_ACF_CODE_READY=1',flush=True)
   print('STUDIO_WRITES_STILL_OFF=1',flush=True)
   print('STUDIO_ORIGINAL_UNCHANGED=1',flush=True)
   print('STUDIO_PRIVATE_ROLLBACK_NAME='+backup.name,flush=True)
   print('STUDIO_PUBLISHED_FILES='+str(len(touched)),flush=True)
  except Exception as e:
   failures=[]
   for rel in reversed(touched):
    try:
     dest=live/rel
     src=archive/rel
     if src.is_file():
      temp=write_atomic(dest,src.read_bytes(),stat.S_IMODE(src.stat().st_mode))
      os.replace(temp,dest)
     elif dest.exists():dest.unlink()
    except Exception as failure:failures.append(rel.as_posix())
   print('STUDIO_DEPLOY_FAILED='+type(e).__name__+':'+str(e),flush=True)
   print('STUDIO_ROLLBACK_CONFIRMED='+str(int(not failures)),flush=True)
   require(not failures,'PARTIAL_ROLLBACK_FAILURE')
   raise
finally:
 shutil.rmtree(stage_parent,ignore_errors=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 mode=os.getenv('STUDIO_DEPLOY_MODE','preflight')
 if mode not in ('preflight','deploy'):raise RuntimeError('INVALID_MODE')
 key,host,port,user=bridge_module.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g6-code-deploy-') as tmp:
  k=pathlib.Path(tmp)/'key';k.write_text(key);k.chmod(0o600)
  h=pathlib.Path(tmp)/'hosts';h.write_text('anthares-studio-g6-release '+bridge_module.HOST_KEY+'\n');h.chmod(0o600)
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-studio-g6-release','-o','ConnectTimeout=12',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  code=REMOTE.replace('MODE_MARKER',mode)
  result=subprocess.run(cmd,input=code,text=True,capture_output=True,timeout=170)
  for line in result.stdout.splitlines():
   if line.startswith('STUDIO_'):print(line,flush=True)
  if result.returncode:
   tail=(result.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   clean=''.join(c if c.isalnum() or c in ' _:-' else '_' for c in tail)[:150]
   print('STUDIO_RELEASE_REMOTE_ERROR='+clean,flush=True)
   raise RuntimeError('REMOTE_RELEASE_FAILED')
  success='STUDIO_RELEASE_PREFLIGHT_PASS=1' if mode=='preflight' else 'STUDIO_CODE_DEPLOY_PROVEN=1'
  if success not in result.stdout:raise RuntimeError('SUCCESS_MARKER_MISSING')
if __name__=='__main__':
 main()
