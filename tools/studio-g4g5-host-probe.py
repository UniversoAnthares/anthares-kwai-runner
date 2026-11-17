#!/usr/bin/env python3
"""One-time read-only Hostinger feasibility probe. No credentials disclosed."""
import json,os,pathlib,socket,subprocess,tempfile,urllib.request
HOST_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA7FQ2RBq0cii+VVCqcB90JxkJRPdurdrX1RGThhKtT2'
def get_ssh_config(token):
    req=urllib.request.Request('https://gitlab.com/api/v4/projects/87361776/variables?per_page=100',
        headers={'PRIVATE-TOKEN':token,'User-Agent':'anthares-studio-g4g5-readonly-probe'})
    with urllib.request.urlopen(req,timeout=20) as response:
        rows=json.load(response)
    values={x.get('key'):x.get('value') for x in rows}
    needed=('ANTHARES_QA_SSH_KEY','ANTHARES_QA_SSH_HOST','ANTHARES_QA_SSH_USER')
    if any(not values.get(x) for x in needed):raise RuntimeError('HOSTINGER_SSH_BRIDGE_UNAVAILABLE')
    host=values['ANTHARES_QA_SSH_HOST'];user=values['ANTHARES_QA_SSH_USER']
    port=str(values.get('ANTHARES_QA_SSH_PORT') or '65002')
    if user!='u566597497' or port!='65002':raise RuntimeError('HOSTINGER_TARGET_UNEXPECTED')
    ips={r[4][0] for r in socket.getaddrinfo(host,None,family=socket.AF_INET)}
    if ips!={'195.35.39.110'}:raise RuntimeError('HOSTINGER_ADDRESS_UNEXPECTED')
    return values['ANTHARES_QA_SSH_KEY'],host,port,user
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
key,host,port,user=get_ssh_config(os.environ['GITLAB_TOKEN'])
with tempfile.TemporaryDirectory(prefix='g4g5-probe-') as tmp:
    k=pathlib.Path(tmp)/'key';k.write_text(key);k.chmod(0o600)
    h=pathlib.Path(tmp)/'known_hosts';h.write_text('anthares-g4g5-probe '+HOST_KEY+'\n')
    cmd=['ssh','-T','-i',str(k),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
         '-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+str(h),
         '-o','HostKeyAlias=anthares-g4g5-probe','-o','ConnectTimeout=10',
         f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
    r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=45)
    for line in r.stdout.splitlines():
        if line.startswith('STUDIO_'):print(line)
    if r.returncode:raise RuntimeError('REMOTE_PROBE_FAILED')
