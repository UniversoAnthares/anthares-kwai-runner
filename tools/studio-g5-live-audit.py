#!/usr/bin/env python3
"""G5 production READ ONLY audit: verify manifest, backups, locks, ACF and 71 records."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('g5_bridge',here/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import hashlib,json,os,pathlib,subprocess
home=pathlib.Path.home();web=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
plugin=web/'wp-content/plugins/anthares-studio'
origin=web/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
source=private/'studio-g6-review-20261116'
def check(b,msg):
 if not b:raise RuntimeError(msg)
def gblob(p):
 d=p.read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
def filehash(p):
 return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ''
check(plugin.is_dir() and origin.is_file() and source.is_dir(),'STUDIO_PATHS_NOT_FOUND')
check(filehash(origin)=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_CHANGED')
check(gblob(plugin/'anthares-estudio.php')=='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb','STUDIO_DEPLOYED_PHP_CHANGED')
for name in ('estudio.css','estudio-dark.css'):
 p=plugin/'assets'/name;check(p.is_file(),'STUDIO_CSS_MISSING')
manifest=source/'anthares-studio/docs/acf-core-migration-map.json'
expected='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325'
check(gblob(manifest)==expected,'SOURCE_MANIFEST_CHANGED')
m=json.loads(manifest.read_text())
check(len(m['entries'])==51 and m['schema_version']=='G5-offline-2026-11-16','BAD_MANIFEST_CONTRACT')
groups=list((plugin/'acf-json').glob('group_anst*.json'))
check(len(groups)==12,'LIVE_ACF_GROUPS_MISSING')
for group in groups:check(json.loads(group.read_text()).get('active') is False,'ACF_GROUP_ACTIVE_UNEXPECTED')
print('G5_LIVE_MANIFEST_PRESENT='+str(int((plugin/'docs/acf-core-migration-map.json').is_file())),flush=True)
print('G5_SOURCE_MANIFEST_SHA='+expected,flush=True)
print('G5_LIVE_OFFLINE_GROUPS='+str(len(groups)),flush=True)
print('G5_BACKUP_CANDIDATES_BEGIN=1',flush=True)
eligible=[]
for d in sorted(private.iterdir()):
 if not d.is_dir() or not d.name.startswith(('studio-g','anthares-studio','studio-backup')):continue
 req=('wordpress-consistent.sql.gz','anthares-estudio-original.tar.gz','restore-verification.txt','backup-sha256.txt')
 if not any((d/k).is_file() for k in req):continue
 b=all((d/k).is_file() for k in req)
 if b:
  restore='RESTORE=PASS' in (d/'restore-verification.txt').read_text(errors='replace')
  index=(d/'backup-sha256.txt').read_text(errors='replace')
  checks=all(filehash(d/k)+'  '+k in index for k in req[:2])
  b=bool(restore and checks)
 print('G5_BACKUP='+d.name+' VERIFIED='+str(int(b)),flush=True)
 if b:eligible.append(d.name)
print('G5_BACKUPS_VERIFIED='+str(len(eligible)),flush=True)
php=r'''define('DISABLE_WP_CRON',true); require 'WPLOAD_MARKER';
global $wpdb;
$count=function($prefix){return (int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN ('{$prefix}_projeto','{$prefix}_nota','{$prefix}_capitulo','{$prefix}_cartao')");};
$state=[
 'old'=>$count('aest'),'new'=>$count('anst'),
 'writes'=>get_option('anst_writes_enabled','0'),
 'cleanup'=>get_option('anst_trash_cleanup_enabled','0'),
 'acf_runtime'=>get_option('anst_acf_runtime_enabled','0'),
 'acf_plugin'=>function_exists('acf_add_local_field_group'),
 'new_plugin'=>in_array('anthares-studio/anthares-estudio.php',(array)get_option('active_plugins',[]),true),
 'old_plugin'=>in_array('anthares-estudio/anthares-estudio.php',(array)get_option('active_plugins',[]),true),
 'free_lock'=>(int)$wpdb->get_var("SELECT IS_FREE_LOCK('anst_acf_migrate_v1')")
];
echo 'G5_STATE='.wp_json_encode($state)."\n";'''
php=php.replace('WPLOAD_MARKER',str(web/'wp-load.php'))
p=subprocess.run(['/opt/alt/php83/usr/bin/php','-r',php],capture_output=True,text=True,timeout=45)
check(p.returncode==0,'WORDPRESS_BOOTSTRAP_ERROR')
raw=next((s.split('=',1)[1] for s in p.stdout.splitlines() if s.startswith('G5_STATE=')),None)
check(raw is not None,'MISSING_WP_OUTPUT')
state=json.loads(raw)
for k in ['old','new']:check(state[k]==71,'RECORD_COUNT_CHANGED_'+k)
for k in ['writes','cleanup','acf_runtime']:check(str(state[k])=='0','FLAG_MISMATCH_'+k)
check(state['acf_plugin'] and state['new_plugin'] and state['old_plugin'],'PLUGIN_INACTIVE')
check(state['free_lock']==1,'MIGRATION_CONCURRENT_LOCK')
print('G5_LIVE_71_71_AND_FLAGS=PASS',flush=True)
print('G5_WP_CLI_FILE='+str(int(pathlib.Path('/usr/local/bin/wp').is_file())),flush=True)
print('G5_AUDIT_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':
  raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-readonly-') as tmp:
  path=pathlib.Path(tmp)
  k=path/'key';k.write_text(key);k.chmod(0o600)
  h=path/'hosts';h.write_text('anthares-g5-audit '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes',
       '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
       '-o','UserKnownHostsFile='+str(h),'-o','HostKeyAlias=anthares-g5-audit',
       '-o','ConnectTimeout=10',f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  p=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=105)
  for line in p.stdout.splitlines():
   if line.startswith('G5_'):print(line,flush=True)
  if p.returncode:
   err=(p.stderr.strip().splitlines() or ['UNCLASSIFIED'])[-1]
   err=''.join(x if x.isalnum() or x in ' _:-' else '_' for x in err)[:125]
   print('G5_AUDIT_ERROR='+err,flush=True)
   raise RuntimeError('G5_READONLY_AUDIT_FAILED')
  if 'G5_AUDIT_PROVEN=1' not in p.stdout:raise RuntimeError('G5_AUDIT_SIGNAL_MISSING')
if __name__=='__main__':main()
