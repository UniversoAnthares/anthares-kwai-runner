#!/usr/bin/env python3
"""One-time read-only Hostinger feasibility probe. No credentials disclosed."""
import importlib.util
import os,pathlib,subprocess,tempfile
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('anthares_existing_ssh',HERE/'studio-css-live-once.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
REMOTE=r"""
import os,pathlib,shutil,subprocess
home=pathlib.Path.home()
private=home/'domains/anthares.us/anthares-private-storage'
root=home/'domains/anthares.us/public_html'
print('STUDIO_PRIVATE_BACKUP_EXISTS='+str(int(private.is_dir())))
print('STUDIO_WP_ROOT_EXISTS='+str(int((root/'wp-load.php').is_file())))
for name in ['node','npm','google-chrome','chromium','chromium-browser','mariadb','mariadbd','mariadb-install-db','php','python3','git','wp']:
 print('STUDIO_HAS_'+name.upper().replace('-','_')+'='+str(int(bool(shutil.which(name)))))
for name in ['studio-g5-baseline-20261116-1738','studio-g1-backup-20261116-1527']:
 print('STUDIO_SNAPSHOT_'+name.split('-')[1].upper()+'='+str(int((private/name).is_dir())))
found=[]
for top in [home,home/'domains/anthares.us',private]:
 try:
  for entry in top.iterdir():
   if entry.is_dir() and any(n in entry.name.lower() for n in ['studio','wordpress','anthares-g','acf']):
    found.append((entry.name,(entry/'.git').is_dir(),(entry/'anthares-studio/tests/integration/g5-runtime-isolated.sh').is_file()))
 except OSError:pass
print('STUDIO_CHECKOUT_CANDIDATES='+repr(found[:35]))
print('STUDIO_WEBROOT_THEME='+str(int((root/'wp-content/themes').is_dir())))
print('STUDIO_LEGACY_PLUGIN_EXISTS='+str(int((root/'wp-content/plugins/anthares-estudio/anthares-estudio.php').is_file())))
print('STUDIO_ACF_PLUGIN_EXISTS='+str(int((root/'wp-content/plugins/advanced-custom-fields/acf.php').is_file())))
print('STUDIO_HAS_BUILTIN_ROUTER=1')
"""
if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('wrong branch')
key,host,port,user=base.get_ssh_config(os.environ['GITLAB_TOKEN'])
with tempfile.TemporaryDirectory(prefix='g4g5-probe-') as tmp:
    k=pathlib.Path(tmp)/'key';k.write_text(key);k.chmod(0o600)
    h=pathlib.Path(tmp)/'known_hosts';h.write_text('anthares-g4g5-probe '+base.HOST_KEY+'\n')
    cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
         '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
         '-o','HostKeyAlias=anthares-g4g5-probe','-o','ConnectTimeout=10',
         f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
    r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=45)
    for line in r.stdout.splitlines():
        if line.startswith('STUDIO_'):print(line)
    if r.returncode:raise RuntimeError('REMOTE_PROBE_FAILED')
