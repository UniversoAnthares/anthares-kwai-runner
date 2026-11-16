#!/usr/bin/env python3
"""Read-only WordPress production inventory for Anthares Studio item 2."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

EXPECTED_REPO='UniversoAnthares/anthares-kwai-runner'
EXPECTED_BRANCH='refs/heads/audit/studio-item2-20261116'
EXPECTED_HOST='195.35.39.110'
EXPECTED_USER='u566597497'
EXPECTED_PORT='65002'
HOST_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA7FQ2RBq0cii+VVCqcB90JxkJRPdurdrX1RGThhKtT2'

REMOTE=r"""
import hashlib, json, os, pathlib, re, shutil, subprocess, sys, urllib.request, urllib.error
home=pathlib.Path.home()
root=home/'domains/anthares.us/public_html'
new=root/'wp-content/plugins/anthares-studio'
old=root/'wp-content/plugins/anthares-estudio'
paths={
 'studio_php':new/'anthares-estudio.php',
 'studio_css':new/'assets/estudio.css',
 'studio_dark_css':new/'assets/estudio-dark.css',
 'legacy_php':old/'anthares-estudio.php'
}
expected={
 'studio_php':'042863a385c5fb8df359c52591bc63a0e033bd9b37e2f8cd8c3992b6d71ad5b7',
 'studio_css':'6fc81afb986db6c427da558fd6ed13218575ea90446cbabd0400a9f8e827de97',
 'studio_dark_css':'2917c1acbfa82098989915b7f1725b729d6345fe920a71398b19f4757563435b',
 'legacy_php':'13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf'
}
def require(flag,label):
 if not flag:
  print('STUDIO_AUDIT_FAILURE='+label,flush=True)
  raise RuntimeError(label)
require(root.is_dir() and new.is_dir() and old.is_dir(),'EXPECTED_SITE_LAYOUT_ABSENT')
for name,p in paths.items():
 require(p.is_file() and not p.is_symlink(),'FILE_MISSING_OR_LINK_'+name)
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 print('FILE_'+name.upper()+'_SHA256='+digest,flush=True)
 require(digest==expected[name],'LIVE_HASH_UNEXPECTED_'+name)
php=paths['studio_php'].read_text(encoding='utf-8')
version=re.search(r'^\s*\*\s*Version:\s*(.+)$',php,re.M)
require(version is not None,'PLUGIN_HEADER_VERSION_NOT_FOUND')
print('INSTALLED_PLUGIN_VERSION='+version.group(1).strip(),flush=True)
assert 'anst-studio-page' in php
assert "get_option('anst_writes_enabled','0')" in php
assert "get_option('anst_trash_cleanup_enabled','0')" in php
assert "new WP_Error('anst_staging_locked'" in php
for p in (paths['studio_css'],paths['studio_dark_css']):
 s=p.read_text(encoding='utf-8')
 require('page-id-19344' not in s and 'post-19344' not in s,'OLD_SELECTOR_REINTRODUCED')
print('STUDIO_CSS_SCOPE=PASS',flush=True)
phpbin='/opt/alt/php83/usr/bin/php'
require(pathlib.Path(phpbin).is_file(),'PHP_83_NOT_AVAILABLE')
lint=subprocess.run([phpbin,'-l',str(paths['studio_php'])],text=True,capture_output=True,timeout=30)
require(lint.returncode==0,'PHP_LINT_ERROR')
print('STUDIO_PHP_LINT=PASS',flush=True)
wp=shutil.which('wp') or next((str(c) for c in (home/'bin/wp',pathlib.Path('/usr/local/bin/wp'),pathlib.Path('/usr/bin/wp')) if c.is_file()),None)
print('STUDIO_WPCLI_AVAILABLE='+str(int(bool(wp))),flush=True)
code=r'''$page=get_page_by_path("studio",OBJECT,"page");
$legacy=get_page_by_path("estudio",OBJECT,"page");
$plugins=(array)get_option("active_plugins",[]);
$writes=(string)get_option("anst_writes_enabled","0");
$cleanup=(string)get_option("anst_trash_cleanup_enabled","0");
$oldUser=get_current_user_id();
wp_set_current_user(106);
$authorized=function_exists("anst_can_use") && anst_can_use();
$get=$authorized && function_exists("anst_permission") ? anst_permission(new WP_REST_Request("GET","/anthares-studio/v1/projects")) : null;
$post=$authorized && function_exists("anst_permission") ? anst_permission(new WP_REST_Request("POST","/anthares-studio/v1/projects")) : null;
wp_set_current_user($oldUser);
$out=array(
 "wp_version"=>get_bloginfo("version"),
 "studio_active"=>in_array("anthares-studio/anthares-estudio.php",$plugins,true),
 "legacy_active"=>in_array("anthares-estudio/anthares-estudio.php",$plugins,true),
 "studio_page_id"=>$page ? (int)$page->ID : null,
 "studio_page_status"=>$page ? $page->post_status : null,
 "legacy_page_exists"=>(bool)$legacy,
 "write_option"=>$writes,
 "cleanup_option"=>$cleanup,
 "permitted_test_account_present"=>(bool)get_user_by("id",106),
 "authorized_role"=>$authorized,
 "get_allowed"=>$get===true,
 "post_denied_with_423"=>is_wp_error($post) && $post->get_error_code()==="anst_staging_locked" && (int)($post->get_error_data()["status"]??0)===423
);
echo "STUDIO_WORDPRESS_AUDIT=".wp_json_encode($out,JSON_UNESCAPED_SLASHES)."\n";'''
# Prefer the real WordPress bootstrap over a CLI shim that can reject noninteractive invocations.
bootstrap='define("WP_USE_THEMES",false);define("DISABLE_WP_CRON",true);require '+json.dumps(str(root/'wp-load.php'))+';'
command=[phpbin,'-d','display_errors=stderr','-r',bootstrap+code]
result=subprocess.run(command,text=True,capture_output=True,timeout=75)
if result.returncode!=0:
 err=result.stderr or ''
 flags=['Parse error','Fatal error','undefined function','database connection','Access denied','permission denied','No such file']
 kind=next((i.replace(' ','_').upper() for i in flags if i.lower() in err.lower()),'UNCLASSIFIED')
 print('STUDIO_AUDIT_FAILURE=PHP_BOOTSTRAP_'+kind,flush=True)
 raise RuntimeError('PHP_BOOTSTRAP_FAILED')
matched=re.search(r'^STUDIO_WORDPRESS_AUDIT=([^\r\n]+)',result.stdout,re.M)
require(matched is not None,'WORDPRESS_AUDIT_NOT_RETURNED')
audit=json.loads(matched.group(1))
for field in ('studio_active','legacy_active','legacy_page_exists','permitted_test_account_present','authorized_role','get_allowed','post_denied_with_423'):
 require(audit[field] is True,'AUDIT_NEGATIVE_'+field)
require(audit['write_option']=='0','WRITE_GATE_ACTIVE_UNEXPECTED')
require(audit['cleanup_option']=='0','TRASH_CLEANUP_ACTIVE_UNEXPECTED')
require(audit['studio_page_status']=='private','STUDIO_PAGE_NOT_PRIVATE')
print('WORDPRESS_VERSION='+str(audit['wp_version']),flush=True)
print('STUDIO_ACTIVE=1 LEGACY_ACTIVE=1',flush=True)
print('STUDIO_PAGE_ID='+str(audit['studio_page_id']),flush=True)
print('STUDIO_PAGE_VISIBILITY='+audit['studio_page_status'],flush=True)
print('WRITES_ENABLED=0 TRASH_CLEANUP_ENABLED=0',flush=True)
print('AUTHORIZED_GET_ALLOWED=1 AUTHORIZED_POST_423=1',flush=True)
req=urllib.request.Request('https://anthares.us/wp-json/anthares-studio/v1/bootstrap',headers={'User-Agent':'Anthares-Studio-Item2-ReadOnly-Audit'})
try:
 with urllib.request.urlopen(req,timeout=15) as response:
  public_status=response.status
except urllib.error.HTTPError as e:
 public_status=e.code
require(public_status in (401,403),'ANONYMOUS_REST_NOT_PROTECTED')
print('ANONYMOUS_REST_STATUS='+str(public_status),flush=True)
print('STUDIO_ITEM2_PROVEN=1',flush=True)
"""

def require(condition,code):
    if not condition: raise RuntimeError(code)

def main():
    require(os.getenv('GITHUB_REPOSITORY')==EXPECTED_REPO,'WRONG_REPO')
    require(os.getenv('GITHUB_REF')==EXPECTED_BRANCH,'WRONG_BRANCH')
    require(os.getenv('GITHUB_EVENT_NAME')=='push','WRONG_EVENT')
    base=Path(__file__).with_name('studio-css-live-once.py')
    spec=importlib.util.spec_from_file_location('anthares_studio_css_bridge',base)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    token=os.environ.get('GITLAB_TOKEN')
    require(bool(token),'GITLAB_PROTECTED_BRIDGE_UNAVAILABLE')
    key,host,port,user=module.get_ssh_config(token)
    require(user==EXPECTED_USER and port==EXPECTED_PORT,'SSH_IDENTITY_MISMATCH')
    with tempfile.TemporaryDirectory(prefix='anthares-studio-item2-') as td:
        folder=Path(td)
        keyfile=folder/'key'
        keyfile.write_text(key)
        keyfile.chmod(0o600)
        knownhosts=folder/'known_hosts'
        knownhosts.write_text('anthares-item2-20261116 '+HOST_KEY+'\n')
        knownhosts.chmod(0o600)
        command=['ssh','-T','-i',str(keyfile),'-p',port,'-o','IdentitiesOnly=yes',
                 '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
                 '-o','UserKnownHostsFile='+str(knownhosts),
                 '-o','HostKeyAlias=anthares-item2-20261116',
                 '-o','ConnectTimeout=12',user+'@'+host,
                 '/opt/alt/python311/bin/python3.11 -']
        result=subprocess.run(command,input=REMOTE,text=True,capture_output=True,timeout=130)
        for line in result.stdout.splitlines():
            if line.startswith(('FILE_','INSTALLED_','STUDIO_','WORDPRESS_','WRITES_','TRASH_','AUTHORIZED_','ANONYMOUS_','LEGACY_')):
                print(line,flush=True)
        require(result.returncode==0,'REMOTE_STUDIO_ITEM2_AUDIT_FAILED')
        require('STUDIO_ITEM2_PROVEN=1' in result.stdout,'SUCCESS_SIGNAL_MISSING')

if __name__=='__main__':
    main()
