#!/usr/bin/env python3
"""Production G5 ACF: preflight & eventually transactional CLI migration. No public Studio writes."""
import importlib.util,os,pathlib,subprocess,tempfile
here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('anthares_g5_bridge',here/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
REMOTE=r"""
import hashlib,json,os,pathlib,re,subprocess,sys,tempfile
MODE='MODE_MARKER'
home=pathlib.Path.home()
site=home/'domains/anthares.us/public_html'
private=home/'domains/anthares.us/anthares-private-storage'
new=site/'wp-content/plugins/anthares-studio'
legacy=site/'wp-content/plugins/anthares-estudio/anthares-estudio.php'
migrator=new/'includes/acf/class-anst-acf-migrator.php'
manifest=new/'docs/acf-core-migration-map.json'
backup=private/'studio-g1-backup-20261116-1527'
php='/opt/alt/php83/usr/bin/php'
wp='/usr/local/bin/wp'
def require(ok,code):
 if not ok:raise RuntimeError(code)
def gitsha(data):
 return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
require(MODE in ('dryrun','apply','verify'),'INVALID_ACF_MODE')
require(site.is_dir() and new.is_dir() and migrator.is_file() and manifest.is_file(),'ACF_REQUIRED_PATH_MISSING')
require(gitsha((new/'anthares-estudio.php').read_bytes())=='0415a16c83a2e0b75dcab5ddd8a7f17511cf07eb','PRODUCTION_PLUGIN_CHANGED')
require(gitsha(manifest.read_bytes())=='b7b7b52b990279adb5cc8f5308c6cbedf1a4b325','ACF_MANIFEST_CHANGED')
require(len(list((new/'acf-json').glob('group_anst*.json')))==12,'ACF_GROUP_COUNT_CHANGED')
require(hashlib.sha256(legacy.read_bytes()).hexdigest()=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_CHANGED')
require(backup.is_dir() and (backup/'restore-verification.txt').is_file(),'RESTORED_BACKUP_UNAVAILABLE')
require('RESTORE=PASS' in (backup/'restore-verification.txt').read_text(),'BACKUP_NOT_RESTORE_VERIFIED')
sha_manifest=(backup/'backup-sha256.txt').read_text()
for f in ('wordpress-consistent.sql.gz','anthares-estudio-original.tar.gz'):
 p=backup/f
 require(p.is_file(),'BACKUP_FILE_MISSING_'+f)
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 require((digest+'  '+f) in sha_manifest,'BACKUP_DIGEST_BAD_'+f)
def run_cli(extras):
 args=[php,wp,'--path='+str(site),'--skip-themes','--no-color']+extras
 p=subprocess.run(args,capture_output=True,text=True,timeout=100)
 if p.returncode:
  msg=(p.stderr or p.stdout or 'FAILED').splitlines()[-1]
  msg=re.sub(r'[^A-Za-z0-9 _.:=-]','_',msg)[:160]
  print('STUDIO_G5_CLI_FAILURE='+msg,flush=True)
  raise RuntimeError('WP_CLI_EXIT_NONZERO')
 return p.stdout
def state():
 code=r'''global $wpdb;$types="'anst_projeto','anst_nota','anst_capitulo','anst_cartao'";
$count=(int)$wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type IN (".$types.")");
$flags=['writes'=>(string)get_option('anst_writes_enabled','0'),
  'cleanup'=>(string)get_option('anst_trash_cleanup_enabled','0'),
  'runtime'=>(string)get_option('anst_acf_runtime_enabled','0')];
echo "STUDIO_STATE=".wp_json_encode(['count'=>$count,'flags'=>$flags])."\n";'''
 r=run_cli(['eval',code])
 line=next((v.split('=',1)[1] for v in r.splitlines() if v.startswith('STUDIO_STATE=')),None)
 require(bool(line),'WP_STATE_MISSING')
 val=json.loads(line)
 require(val['count']==71,'ANST_SOURCE_COUNT_CHANGED')
 require(all(v=='0' for v in val['flags'].values()),'PRODUCTION_OPTION_GATE_CHANGED')
 return val
def dry():
 out=run_cli(['--require='+str(migrator),'anst-acf-migrate'])
 props={}
 for line in out.splitlines():
  if '=' in line and line.split('=',1)[0] in (
   'SOURCE_COUNT','SOURCE_META_COUNT','SOURCE_FINGERPRINT',
   'ACF_TARGET_PRESENT','ACF_TARGET_EXISTING','ZOOM_USER_COUNT',
   'ACF_COURSE_JSON_BYTES','REFERENCE_ERRORS'):
   key,value=line.split('=',1);props[key]=value
 for key in ('SOURCE_COUNT','SOURCE_META_COUNT','SOURCE_FINGERPRINT','ACF_TARGET_PRESENT',
             'ACF_TARGET_EXISTING','ZOOM_USER_COUNT','REFERENCE_ERRORS'):
  require(key in props,'DRYRUN_MISSING_'+key)
 require(props['SOURCE_COUNT']=='71','SOURCE_COUNT_CHANGED')
 require(props['ACF_TARGET_PRESENT']=='412','TARGET_FIELD_COUNT_CHANGED')
 require(props['ZOOM_USER_COUNT']=='1','USER_ZOOM_COUNT_CHANGED')
 require(props['REFERENCE_ERRORS']=='0','REFERENCE_ERRORS_DETECTED')
 require(re.fullmatch('[a-f0-9]{64}',props['SOURCE_FINGERPRINT']) is not None,'FINGERPRINT_INVALID')
 return props
state()
before=dry()
print('STUDIO_G5_SOURCE_COUNT='+before['SOURCE_COUNT'],flush=True)
print('STUDIO_G5_SOURCE_FINGERPRINT='+before['SOURCE_FINGERPRINT'],flush=True)
print('STUDIO_G5_SOURCE_META_COUNT='+before['SOURCE_META_COUNT'],flush=True)
print('STUDIO_G5_ACF_TARGET_PRESENT='+before['ACF_TARGET_PRESENT'],flush=True)
print('STUDIO_G5_ACF_TARGET_EXISTING='+before['ACF_TARGET_EXISTING'],flush=True)
print('STUDIO_G5_ZOOM_USER_COUNT='+before['ZOOM_USER_COUNT'],flush=True)
print('STUDIO_G5_REFERENCE_ERRORS='+before['REFERENCE_ERRORS'],flush=True)
print('STUDIO_G5_BACKUP_VERIFIED=1',flush=True)
if MODE=='dryrun':
 again=dry()
 require(before['SOURCE_FINGERPRINT']==again['SOURCE_FINGERPRINT'],'SOURCE_DRIFT_IN_READONLY')
 print('STUDIO_G5_LIVE_DRYRUN_PROVEN=1',flush=True)
elif MODE=='apply':
 require(before['ACF_TARGET_EXISTING'] in ('0','414'),'PREEXISTING_ACF_INCONSISTENT')
 helper=tempfile.NamedTemporaryFile(prefix='.anst-g5-cli-',suffix='.php',dir=str(private),delete=False)
 try:
  helper.write(b"<?php if(!defined('ANST_ALLOW_ACF_WRITE')) define('ANST_ALLOW_ACF_WRITE',true);\n")
  helper.flush();os.fsync(helper.fileno());helper.close()
  os.chmod(helper.name,0o600)
  args=['--require='+helper.name,'--require='+str(migrator),'anst-acf-migrate',
        '--apply','--expected-fingerprint='+before['SOURCE_FINGERPRINT'],
        '--backup-dir='+str(backup)]
  first=run_cli(args)
  match=re.search(r'ACF_APPLY_VERIFIED written=(\d+) skipped=(\d+)',first)
  require(match is not None,'ACF_FIRST_APPLY_UNVERIFIED')
  if before['ACF_TARGET_EXISTING']=='414':
   require(match.group(1)=='0' and match.group(2)=='414','ACF_REAPPLY_NOT_IDEMPOTENT')
  else:
   require(match.group(1)=='414' and match.group(2)=='0','ACF_FIRST_WRITE_NOT_414')
  print('STUDIO_G5_FIRST_WRITTEN='+match.group(1)+' SKIPPED='+match.group(2),flush=True)
  second=run_cli(args)
  match2=re.search(r'ACF_APPLY_VERIFIED written=(\d+) skipped=(\d+)',second)
  require(match2 is not None and match2.group(1)=='0' and match2.group(2)=='414','ACF_SECOND_APPLY_NOT_IDEMPOTENT')
  print('STUDIO_G5_SECOND_WRITTEN=0 SKIPPED=414',flush=True)
 finally:
  if os.path.isfile(helper.name):os.unlink(helper.name)
 post=dry()
 require(post['SOURCE_FINGERPRINT']==before['SOURCE_FINGERPRINT'],'LEGACY_META_CHANGED')
 require(post['ACF_TARGET_EXISTING']=='414','ACF_TARGET_POSTCOUNT_BAD')
 state()
 require(hashlib.sha256(legacy.read_bytes()).hexdigest()=='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf','LEGACY_CHANGED_AFTER_MIGRATION')
 print('STUDIO_G5_MIGRATION_APPLY_PROVEN=1',flush=True)
 print('STUDIO_G5_LEGACY_DATA_UNCHANGED=1',flush=True)
 print('STUDIO_G5_RUNTIME_STILL_OFF=1',flush=True)
elif MODE=='verify':
 require(before['ACF_TARGET_EXISTING']=='414','ACF_TARGETS_NOT_ALL_PRESENT')
 print('STUDIO_G5_READONLY_VERIFY_PROVEN=1',flush=True)
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 mode=os.getenv('STUDIO_G5_MODE','dryrun')
 if mode not in ('dryrun','apply','verify'):raise RuntimeError('INVALID_MODE')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='studio-g5-live-cli-') as temp:
  k=pathlib.Path(temp)/'key';k.write_text(key);k.chmod(0o600)
  h=pathlib.Path(temp)/'hosts';h.write_text('anthares-g5-cli '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
       '-o','HostKeyAlias=anthares-g5-cli','-o','ConnectTimeout=12',
       f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  p=subprocess.run(cmd,input=REMOTE.replace('MODE_MARKER',mode),text=True,capture_output=True,timeout=270)
  for line in p.stdout.splitlines():
   if line.startswith('STUDIO_'):print(line,flush=True)
  if p.returncode:
   tail=(p.stderr.strip().splitlines() or ['UNKNOWN_REMOTE_ERROR'])[-1]
   print('STUDIO_G5_REMOTE_ERROR='+''.join(c if c.isalnum() or c in ' _:-' else '_' for c in tail)[:150],flush=True)
   raise RuntimeError('PRODUCTION_ACF_CLI_FAILED')
  expected={
   'dryrun':'STUDIO_G5_LIVE_DRYRUN_PROVEN=1',
   'apply':'STUDIO_G5_MIGRATION_APPLY_PROVEN=1',
   'verify':'STUDIO_G5_READONLY_VERIFY_PROVEN=1'
  }[mode]
  if expected not in p.stdout:raise RuntimeError('REQUIRED_G5_EVIDENCE_MISSING')
if __name__=='__main__':
 main()
