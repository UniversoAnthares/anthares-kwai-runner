#!/usr/bin/env python3
"""One-time 2-line ACF approval gate code preparation. Production runtime option stays OFF."""
import importlib.util,os,pathlib,subprocess,tempfile
dir=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g5_bridge',dir/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import datetime,hashlib,os,pathlib,subprocess,tempfile,shutil
home=pathlib.Path.home();web=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
main=web/'wp-content/plugins/anthares-studio/anthares-estudio.php'
legacy=web/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
old_blob='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb'
new_blob='16f5c01457085e73fcde291717ba46ebdbdb2801'
original_sha='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'
def need(ok,code):
 if not ok:raise RuntimeError(code)
def blob(data):
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def wp_check():
 php=r'''define('DISABLE_WP_CRON',true);require 'WPLOAD_MARKER';
global $wpdb;
$ct=function($prefix)use($wpdb){
 return (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('{$prefix}_projeto','{$prefix}_nota','{$prefix}_capitulo','{$prefix}_cartao')");
};
$ok=$ct('aest')===71&&$ct('anst')===71 &&
 (string)get_option('anst_acf_runtime_enabled','0')==='0' &&
 (string)get_option('anst_writes_enabled','0')==='0' &&
 (string)get_option('anst_trash_cleanup_enabled','0')==='0';
echo 'G5_PREP_WP_SAFE='.(int)$ok."\n";'''
 php=php.replace('WPLOAD_MARKER',str(web/'wp-load.php'))
 p=subprocess.run(['/opt/alt/php83/usr/bin/php','-r',php],text=True,capture_output=True,timeout=40)
 need(p.returncode==0 and 'G5_PREP_WP_SAFE=1' in p.stdout,'WORDPRESS_STATE_UNSAFE')
 need(hashlib.sha256(legacy.read_bytes()).hexdigest()==original_sha,'LEGACY_CHANGED')
def atomic(path,data):
 fd,name=tempfile.mkstemp(prefix='.g5prep-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chmod(name,0o644)
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
need(main.is_file() and not main.is_symlink() and private.is_dir(),'PATHS_INVALID')
before=main.read_bytes()
need(blob(before)==old_blob,'LIVE_PHP_CHANGED_CONCURRENTLY')
need(b'ANST_ACF_RUNTIME_APPROVED' not in before,'APPROVAL_ALREADY_EXISTS')
wp_check()
needle=b"if (!defined('ABSPATH')) { exit; }\n"
insertion=(b"// A ativacao do repositorio ACF exige tambem anst_acf_runtime_enabled=1; OFF mantem o legado.\n"
           b"if (!defined('ANST_ACF_RUNTIME_APPROVED')) { define('ANST_ACF_RUNTIME_APPROVED', true); }\n")
# The approved branch contains accented Portuguese; target bytes must match the exact Git blob.
insertion=("// A ativação do repositório ACF exige também anst_acf_runtime_enabled=1; OFF mantém o legado.\n"
           "if (!defined('ANST_ACF_RUNTIME_APPROVED')) { define('ANST_ACF_RUNTIME_APPROVED', true); }\n").encode('utf8')
need(before.count(needle)==1,'INJECTION_POINT_CHANGED')
after=before.replace(needle,needle+insertion)
need(blob(after)==new_blob,'APPROVED_GIT_BLOB_MISMATCH')
lint=subprocess.run(['/opt/alt/php83/usr/bin/php','-l'],input=after,text=False,capture_output=True,timeout=15)
# php -l stdin does not require the script to exist in the public directory.
need(lint.returncode==0,'APPROVAL_PHP_LINT_FAILED')
snapshot=private/('studio-g5-approval-code-backup-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
need(not snapshot.exists(),'BACKUP_CONFLICT')
snapshot.mkdir(mode=0o700)
(snapshot/'anthares-estudio.php').write_bytes(before)
os.chmod(snapshot/'anthares-estudio.php',0o600)
need((snapshot/'anthares-estudio.php').read_bytes()==before,'BACKUP_COMPARE_FAILED')
try:
 need(blob(main.read_bytes())==old_blob,'LIVE_RACE_DETECTED')
 atomic(main,after)
 need(blob(main.read_bytes())==new_blob,'NEW_FILE_HASH_MISMATCH')
 wp_check()
 print('G5_APPROVAL_CODE_DEPLOYED=1',flush=True)
 print('G5_APPROVED_BLOB='+new_blob,flush=True)
 print('G5_PRODUCTION_ACF_RUNTIME=OFF',flush=True)
 print('G5_PRODUCTION_WRITES=OFF',flush=True)
 print('G5_PRODUCTION_LEGACY=UNCHANGED',flush=True)
 print('G5_APPROVAL_BACKUP_NAME='+snapshot.name,flush=True)
except:
 atomic(main,before)
 need(blob(main.read_bytes())==old_blob,'APPROVAL_ROLLBACK_FAILED')
 print('G5_APPROVAL_ROLLBACK=COMPLETE',flush=True)
 raise
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='g5approval-') as t:
  d=pathlib.Path(t);k=d/'key';k.write_text(key);k.chmod(0o600)
  h=d/'hosts';h.write_text('anthares-g5approval '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5approval','-o','ConnectTimeout=10',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  result=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=110)
  for line in result.stdout.splitlines():
   if line.startswith('G5_'):print(line,flush=True)
  if result.returncode:
   err=(result.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G5_APPROVAL_ERROR='+''.join(c if c.isalnum() or c in ' _:.=' else '_' for c in err)[:140],flush=True)
   raise RuntimeError('G5_APPROVAL_DEPLOY_FAILED')
  if 'G5_APPROVAL_CODE_DEPLOYED=1' not in result.stdout:raise RuntimeError('DEPLOY_SIGNAL_MISSING')
if __name__=='__main__':main()
