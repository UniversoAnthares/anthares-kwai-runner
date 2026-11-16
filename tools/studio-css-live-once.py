#!/usr/bin/env python3
"""One-time guarded CSS-only deployment for private Anthares Studio, via existing protected Hostinger SSH bridge."""
import hashlib
import json
import os
import pathlib
import socket
import subprocess
import tempfile
import urllib.request

EXPECTED_REPO = 'UniversoAnthares/anthares-kwai-runner'
EXPECTED_BRANCH = 'refs/heads/fix/studio-css-live-20261116'
HOSTINGER_IP = '195.35.39.110'
HOSTINGER_USER = 'u566597497'
HOSTINGER_PORT = '65002'
# Verified against the owner's SSH known_hosts 2026-11-16, public host key only.
HOST_KEY = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA7FQ2RBq0cii+VVCqcB90JxkJRPdurdrX1RGThhKtT2'
HOST_KEY_ALIAS = 'anthares-css-20261116'

REMOTE_SCRIPT = r"""
import datetime, hashlib, os, pathlib, re, shutil, stat, subprocess, sys, tempfile

home=pathlib.Path.home()
site=home/'domains/anthares.us/public_html/wp-content/plugins'
new=site/'anthares-studio'
old=site/'anthares-estudio'
private=home/'domains/anthares.us/anthares-private-storage'
paths=[new/'assets/estudio.css',new/'assets/estudio-dark.css',new/'anthares-estudio.php']
original_php=old/'anthares-estudio.php'
sha=lambda b: hashlib.sha256(b).hexdigest()
expected_css={
 'estudio.css':'cc50278d75bc6a42d0c1bc6941e659b8372191266aef4760762189c06de973ee',
 'estudio-dark.css':'ad8d92fb38caf7afecc2409b3bcced8c0e63446b2a27776972b55dfface19a92',
}
orig_expected='13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'
def require(condition,reason):
 if not condition: raise RuntimeError(reason)
def lint(path):
 r=subprocess.run(['/opt/alt/php83/usr/bin/php','-l',str(path)],capture_output=True,text=True,timeout=20)
 require(r.returncode==0,'PHP_LINT_FAILED')
def write_stage(path,payload,mode):
 fd,name=tempfile.mkstemp(prefix='.anst-css-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:
   f.write(payload);f.flush();os.fsync(f.fileno())
  os.chmod(name,stat.S_IMODE(mode))
  return pathlib.Path(name)
 except:
  if os.path.exists(name):os.unlink(name)
  raise
def no_symlink(path):
 require(path.is_file() and not path.is_symlink(),'EXPECTED_FILE_INVALID:'+path.name)
 require(path.resolve().is_relative_to(new.resolve()),'PATH_OUTSIDE_NEW_PLUGIN')
 require(path.stat().st_uid==os.geteuid(),'FILE_OWNER_MISMATCH')
def replace_php(data):
 regex=(rb"add_filter\('body_class', function\(\$classes\)\{\s*"
 rb"if\(is_page\('studio'\) && \(!is_user_logged_in\(\) \|\| !anst_can_use\(\)\)\)"
 rb"\$classes\[\]='aest-access-gate';\s*return \$classes;\s*\}\);")
 replacement=(b"add_filter('body_class', function($classes){\n"
 b" if (is_page('studio')) {\n"
 b"  // Escopo estavel e exclusivo da copia; sem depender do ID da pagina WordPress.\n"
 b"  $classes[] = 'anst-studio-page';\n"
 b"  if (!is_user_logged_in() || !anst_can_use()) $classes[] = 'aest-access-gate';\n"
 b" }\n"
 b" return $classes;\n"
 b"});")
 require(len(re.findall(regex,data))==1,'PHP_BODY_FILTER_UNEXPECTED')
 return re.sub(regex,lambda match:replacement,data)
require(site.is_dir() and new.is_dir() and old.is_dir(),'STUDIO_PATH_MISSING')
require(private.is_dir() and not private.is_symlink(),'PRIVATE_BACKUP_DIR_MISSING')
require(original_php.is_file() and sha(original_php.read_bytes())==orig_expected,'LEGACY_BASELINE_CHANGED')
sources={}
targets={}
modes={}
for p in paths:
 no_symlink(p)
 sources[p]=p.read_bytes()
 modes[p]=p.stat().st_mode
 require(len(sources[p])<3_000_000,'UNEXPECTED_FILE_SIZE')
for p in paths[:2]:
 require(sha(sources[p])==expected_css[p.name],'CSS_BASELINE_CHANGED:'+p.name)
 targets[p]=sources[p].replace(b'page-id-19344',b'anst-studio-page')
 if p.name=='estudio.css':
  require(sources[p].count(b'page-id-19344')==509,'MAIN_SELECTOR_COUNT_CHANGED')
  require(sources[p].count(b'article#post-19344')==6,'ARTICLE_SELECTOR_COUNT_CHANGED')
  targets[p]=targets[p].replace(b'article#post-19344',b'article')
 else: require(sources[p].count(b'page-id-19344')==216,'DARK_SELECTOR_COUNT_CHANGED')
 require(b'page-id-19344' not in targets[p] and b'post-19344' not in targets[p],'UNCONVERTED_SELECTOR')
 require(b'body.anst-studio-page' in targets[p],'NEW_SCOPE_ABSENT')
php=paths[2]
require(b"get_option('anst_writes_enabled','0')" in sources[php] and b"'anst_staging_locked'" in sources[php],'WRITE_GATE_MISSING')
targets[php]=replace_php(sources[php])
require(b"'anst-studio-page'" in targets[php],'BODY_SCOPE_MISSING')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
backup=private/('studio-css-rollback-'+stamp)
require(not backup.exists(),'BACKUP_DIR_CONFLICT')
backup.mkdir(mode=0o700)
saved=[]
staged={}
applied=[]
try:
 for p in paths:
  dest=backup/p.name
  with open(dest,'xb') as f:
   f.write(sources[p]);f.flush();os.fsync(f.fileno())
  os.chmod(dest,0o600)
  require(sha(dest.read_bytes())==sha(sources[p]),'BACKUP_HASH_FAILED')
  saved.append(dest)
  staged[p]=write_stage(p,targets[p],modes[p])
 lint(staged[php])
 for p in paths:
  require(p.read_bytes()==sources[p],'CONCURRENT_CHANGE_'+p.name)
 for p in paths:
  os.replace(staged[p],p)
  applied.append(p)
 for p in paths:
  require(p.read_bytes()==targets[p],'POSTWRITE_MISMATCH_'+p.name)
 lint(php)
 require(sha(original_php.read_bytes())==orig_expected,'LEGACY_CHANGED_DURING_APPLY')
 print('STUDIO_CSS_DEPLOY_PROVEN=1',flush=True)
 print('STUDIO_CSS_MAIN_OLD=0 DARK_OLD=0 NEW_SCOPE=PASS',flush=True)
 print('LEGACY_PHP_UNCHANGED=1',flush=True)
 print('BACKUP_PRIVATE_PROVEN=1 name='+backup.name,flush=True)
 print('WRITE_GATE_PRESERVED=1',flush=True)
 for p in paths:print('STUDIO_FILE_SHA256 '+p.name+' '+sha(targets[p]),flush=True)
except Exception as exc:
 for p in reversed(applied):
  try:
   restored=write_stage(p,sources[p],modes[p])
   os.replace(restored,p)
  except Exception as rollback_exc:
   print('ROLLBACK_FAILED '+p.name+' '+type(rollback_exc).__name__,file=sys.stderr,flush=True)
 for p in paths:
  tmp=staged.get(p)
  if tmp and tmp.exists():tmp.unlink()
 ok=all(p.read_bytes()==sources[p] for p in paths)
 print('DEPLOY_FAILED_REASON='+type(exc).__name__+':'+str(exc),file=sys.stderr,flush=True)
 print('ROLLBACK_CONFIRMED='+str(int(ok)),file=sys.stderr,flush=True)
 raise
finally:
 for tmp in staged.values():
  if tmp.exists():tmp.unlink()
"""

def require(flag, reason):
    if not flag:
        raise RuntimeError(reason)

def get_ssh_config(token):
    req = urllib.request.Request(
        'https://gitlab.com/api/v4/projects/87361776/variables?per_page=100',
        headers={'PRIVATE-TOKEN': token, 'User-Agent': 'anthares-studio-css-once'}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        values = {x.get('key'): x.get('value') for x in json.load(response)}
    for key in ('ANTHARES_QA_SSH_KEY','ANTHARES_QA_SSH_HOST','ANTHARES_QA_SSH_USER'):
        require(values.get(key), 'EXISTING_HOSTINGER_BRIDGE_UNAVAILABLE')
    host = values['ANTHARES_QA_SSH_HOST']
    port = str(values.get('ANTHARES_QA_SSH_PORT') or '65002')
    user = values['ANTHARES_QA_SSH_USER']
    require(port == HOSTINGER_PORT and user == HOSTINGER_USER, 'UNEXPECTED_SSH_TARGET')
    ips = {item[4][0] for item in socket.getaddrinfo(host, None, family=socket.AF_INET)}
    require(ips == {HOSTINGER_IP}, 'HOSTINGER_IP_UNEXPECTED')
    return values['ANTHARES_QA_SSH_KEY'], host, port, user

def main():
    require(os.getenv('GITHUB_REPOSITORY')==EXPECTED_REPO, 'WRONG_REPOSITORY')
    require(os.getenv('GITHUB_REF')==EXPECTED_BRANCH, 'WRONG_BRANCH')
    require(os.getenv('GITHUB_EVENT_NAME')=='push', 'WRONG_TRIGGER')
    token=os.environ.get('GITLAB_TOKEN','')
    require(token, 'GITLAB_TOKEN_UNAVAILABLE')
    ssh_key,host,port,user=get_ssh_config(token)
    print('HOSTINGER_PROTECTED_BRIDGE_FOUND=1',flush=True)
    with tempfile.TemporaryDirectory(prefix='studio-css-once-') as folder:
        folder=pathlib.Path(folder)
        keypath=folder/'id_ed25519'
        keypath.write_text(ssh_key)
        keypath.chmod(0o600)
        knownhosts=folder/'known_hosts'
        knownhosts.write_text(f'{HOST_KEY_ALIAS} {HOST_KEY}\n')
        knownhosts.chmod(0o600)
        cmd=['ssh','-T','-i',str(keypath),'-p',port,
             '-o','IdentitiesOnly=yes','-o','BatchMode=yes',
             '-o','StrictHostKeyChecking=yes',
             '-o','UserKnownHostsFile='+str(knownhosts),
             '-o','HostKeyAlias='+HOST_KEY_ALIAS,
             '-o','ConnectTimeout=12',
             f'{user}@{host}', '/opt/alt/python311/bin/python3.11 -']
        result=subprocess.run(cmd,input=REMOTE_SCRIPT,text=True,
                              capture_output=True,timeout=110)
        for line in result.stdout.splitlines():
            if line.startswith(('STUDIO_','LEGACY_','BACKUP_','WRITE_','ROLLBACK_','DEPLOY_')):
                print(line,flush=True)
        for line in result.stderr.splitlines():
            if line.startswith(('ROLLBACK_','DEPLOY_')):
                print(line,flush=True)
        require(result.returncode==0, 'HOSTINGER_DEPLOY_REJECTED_OR_FAILED')
        require('STUDIO_CSS_DEPLOY_PROVEN=1' in result.stdout,'REMOTE_SUCCESS_SIGNAL_MISSING')
        print('STUDIO_CSS_CI_SUCCESS=1',flush=True)

if __name__=='__main__':
    main()
