#!/usr/bin/env python3
"""Read-only production count/hash audit for missing _anst_events ACF field."""
import importlib.util,os,pathlib,subprocess,tempfile
p=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('bridge',p/'studio-g5g6-isolated-qa.py')
bridge=importlib.util.module_from_spec(sp);sp.loader.exec_module(bridge)
REMOTE=r"""
import pathlib,subprocess,re
root=pathlib.Path.home()/'domains/anthares.us/public_html'
php=r'''define('DISABLE_WP_CRON',true);require 'WORDPRESS_BOOT';
global $wpdb;
$sql="SELECT COUNT(*) FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID=m.post_id WHERE m.meta_key='_anst_events' AND p.post_type='anst_projeto'";
$sql2="SELECT COUNT(*) FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID=m.post_id WHERE m.meta_key='studio_events' AND p.post_type='anst_projeto'";
$a=(int)$wpdb->get_var($sql);$b=(int)$wpdb->get_var($sql2);
$ok=(string)get_option('anst_acf_runtime_enabled','0')==='1' &&
    (string)get_option('anst_writes_enabled','0')==='0' &&
    (string)get_option('anst_trash_cleanup_enabled','0')==='0';
echo 'G4_EVENTS_LEGACY_COUNT='.$a."\n";
echo 'G4_EVENTS_ACF_COUNT='.$b."\n";
echo 'G4_EVENTS_STUDIO_SAFE='.(int)$ok."\n";'''
php=php.replace('WORDPRESS_BOOT',str(root/'wp-load.php'))
p=subprocess.run(['/opt/alt/php83/usr/bin/php','-r',php],capture_output=True,text=True,timeout=40)
if p.returncode:raise RuntimeError('WP_EVENTS_READONLY_AUDIT_FAILED')
for line in p.stdout.splitlines():
 if line.startswith('G4_EVENTS_'):print(line,flush=True)
if 'G4_EVENTS_STUDIO_SAFE=1' not in p.stdout:raise RuntimeError('CURRENT_FLAGS_UNSAFE')
"""
def main():
 if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
 key,host,port,user=bridge.bridge(os.environ['GITLAB_TOKEN'])
 with tempfile.TemporaryDirectory(prefix='g4-events-audit-') as t:
  d=pathlib.Path(t);k=d/'key';k.write_text(key);k.chmod(0o600)
  h=d/'hosts';h.write_text('anthares-g4-events '+bridge.HOST_KEY+'\n')
  cmd=['ssh','-T','-i',str(k),'-p',port,'-o','BatchMode=yes','-o','IdentitiesOnly=yes',
       '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),'-o','HostKeyAlias=anthares-g4-events',
       '-o','ConnectTimeout=10',f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
  r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=95)
  for line in r.stdout.splitlines():
   if line.startswith('G4_EVENTS_'):print(line,flush=True)
  if r.returncode:
   last=(r.stderr.strip().splitlines() or ['UNKNOWN'])[-1]
   print('G4_EVENTS_AUDIT_ERROR='+''.join(c if c.isalnum() or c in ' _:.-' else '_' for c in last)[:140],flush=True)
   raise RuntimeError('G4_EVENTS_AUDIT_REMOTE_FAILED')
  if 'G4_EVENTS_STUDIO_SAFE=1' not in r.stdout:raise RuntimeError('G4_EVENTS_AUDIT_INCOMPLETE')
if __name__=='__main__':main()
