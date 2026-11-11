#!/usr/bin/env python3
"""Hostinger-only, source GitHub -> Forgejo; never force, prune, publish or alter CI."""
import datetime,fcntl,json,os,pathlib,re,subprocess,sys,shlex,stat,time
base=pathlib.Path.home()/'.anthares-forgejo'
dest='https://anthares.us/forgejo/anthares-admin/'
names=['anthares-ara-queue','anthares-clipper','anthares-governance','anthares-kwai-runner','anthares-memu4-remote-lab','anthares-memu4-remote-probe','anthares-telegram-relay','anthares-transcricao','anthares-wordpress','github-slideshow','home','wiki','anthares-browser-state','anthares-kwai-session-vault']
public={'anthares-kwai-runner','anthares-memu4-remote-probe','anthares-transcricao','github-slideshow','home','wiki'}
preexisting={'anthares-video-studio':'SEPARATE_AUTHORIZED_HOSTINGER_MIRROR'}
data=base/'data/repositories/anthares-admin'
ask=base/'mirror-avs-askpass.sh'
token_file=base/'keys/github-mirror-readonly.token'
github_askpass=base/'git-mirror-github-askpass.sh'
state=base/'git-mirror-hostinger-status.json'
lock=base/'git-mirror-hostinger.lock'
env=dict(os.environ)
env['GIT_TERMINAL_PROMPT']='0'
env['GIT_ASKPASS']=str(ask)
env['GIT_CONFIG_NOSYSTEM']='1'
env['GIT_CONFIG_GLOBAL']=os.devnull
deploy_key_repos={'anthares-memu4-remote-lab', 'anthares-governance', 'anthares-browser-state', 'anthares-clipper', 'anthares-telegram-relay', 'anthares-kwai-session-vault', 'anthares-ara-queue'}
def source_key_repo(args):
 found=[n for n in deploy_key_repos if any(str(a).endswith('/'+n+'.git') for a in args)]
 if len(found)>1:raise RuntimeError('AMBIGUOUS_SOURCE_REPOSITORY')
 return found[0] if found else None

def run(args,timeout=20,github=False):
 e=dict(env)
 key_repo=source_key_repo(args) if github else None
 if key_repo:
  key=base/'keys'/('gh-readonly-'+key_repo)
  if key.is_symlink() or not key.is_file() or key.stat().st_uid!=os.getuid() or stat.S_IMODE(key.stat().st_mode)&0o077:raise RuntimeError('SOURCE_KEY_PERMISSIONS_UNSAFE')
  e['GIT_SSH_COMMAND']='ssh -F /dev/null -i '+shlex.quote(str(key))+' -o IdentitiesOnly=yes -o IdentityAgent=none -o BatchMode=yes -o StrictHostKeyChecking=yes -o HostKeyAlgorithms=ssh-ed25519 -o UserKnownHostsFile='+shlex.quote(str(base/'keys/github-known-hosts-ed25519'))+' -o ConnectTimeout=8'
 if github and token_file.is_file() and token_file.stat().st_size:
  e['GIT_ASKPASS']=str(github_askpass)
 # The Kwai GitHub source is public; prevent a stale private credential helper
 # from being sent when GitHub challenges. Other private sources keep their auth.
 public_kwai=github and 'https://github.com/UniversoAnthares/anthares-kwai-runner.git' in args
 if public_kwai:
  e['GIT_ASKPASS']='/bin/false'
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,env=e,timeout=timeout)
 if p.returncode:
  error=(p.stderr or '').lower()
  if 'resource temporarily unavailable' in error:raise RuntimeError('HOSTING_PROCESS_LIMIT')
  if public_kwai:
   # Publish only allowlisted diagnostics; never expose credentials or stderr.
   if 'requested url returned error: 403' in error:raise RuntimeError('PUBLIC_GITHUB_HTTP_403')
   if 'requested url returned error: 429' in error:raise RuntimeError('PUBLIC_GITHUB_HTTP_429')
   if 'authentication failed' in error or 'could not read username' in error:raise RuntimeError('PUBLIC_GITHUB_AUTH_CHALLENGE')
   if 'could not resolve host' in error:raise RuntimeError('PUBLIC_GITHUB_DNS_UNAVAILABLE')
   if 'ssl' in error or 'tls' in error or 'certificate' in error:raise RuntimeError('PUBLIC_GITHUB_TLS_UNAVAILABLE')
   raise RuntimeError('PUBLIC_GITHUB_GIT_'+str(p.returncode))
  raise RuntimeError('GIT_FAILED_'+str(p.returncode))
 return p.stdout
def refs(lines):
 d={}
 for l in lines.splitlines():
  x=l.split()
  if len(x)!=2:raise RuntimeError('INVALID_REF_FORMAT')
  sha,name=x
  if not re.match(r'^[0-9a-f]{40}$',sha) or not re.match(r'^refs/(heads|tags)/[A-Za-z0-9_.+/-]+$',name):
   raise RuntimeError('INVALID_REF')
  d[name]=sha
 return d
def verify_repo(name):
 path=data/(name+'.git')
 if not path.is_dir():raise RuntimeError('FORGEJO_REPO_MISSING')
 if name in public:
  source='https://github.com/UniversoAnthares/'+name+'.git'
 elif name in deploy_key_repos or name=='anthares-wordpress':
  source='git@github.com:UniversoAnthares/'+name+'.git'
 else:
  source=('https://github.com/UniversoAnthares/'+name+'.git') if (token_file.is_file() and token_file.stat().st_size) else ('git@github.com:UniversoAnthares/'+name+'.git')
 target=dest+name+'.git'
 is_private=name not in public
 import sqlite3
 con=sqlite3.connect('file:'+str(base/'data/forgejo.db')+'?mode=ro',uri=True)
 row=con.execute('select is_private from repository where name=?',(name,)).fetchone();con.close()
 if not row or bool(row[0])!=is_private:raise RuntimeError('FORGEJO_VISIBILITY_UNEXPECTED')
 try:s=refs(run(['git','ls-remote','--refs',source,'refs/heads/*','refs/tags/*'],timeout=22,github=True))
 except RuntimeError as e:
  if str(e)=='HOSTING_PROCESS_LIMIT' or str(e).startswith('PUBLIC_GITHUB_'):raise
  raise RuntimeError('GITHUB_SOURCE_NOT_AUTHORIZED_OR_UNAVAILABLE')
 try:d=refs(run(['git','--git-dir='+str(path),'for-each-ref','--format=%(objectname) %(refname)','refs/heads','refs/tags'],timeout=22))
 except RuntimeError:raise RuntimeError('FORGEJO_LOCAL_REFS_UNAVAILABLE')
 if not s:
  if d:raise RuntimeError('EMPTY_SOURCE_TARGET_HAS_REFS')
  return {'state':'EMPTY_SOURCE_MATCH','refs':0,'sha':''}
 if 'refs/heads/main' not in s:raise RuntimeError('GITHUB_MAIN_UNAVAILABLE')
 needed={k:v for k,v in s.items() if d.get(k)!=v}
 if not needed:return {'state':'VERIFIED_ALL_SOURCE_REFS','refs':len(s),'sha':s['refs/heads/main']}
 # Fast-forward-only and append-only. Never rewrite or remove existing Forgejo references.
 mirror=base/'git-mirror-hostinger'/(name+'.git')
 mirror.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
 if not mirror.exists():run(['git','clone','--mirror','--quiet',source,str(mirror)],timeout=65,github=True)
 else:
  old=run(['git','--git-dir='+str(mirror),'remote','get-url','origin'],timeout=6).strip()
  if old!=source:
   if name in deploy_key_repos and old=='https://github.com/UniversoAnthares/'+name+'.git' and source=='git@github.com:UniversoAnthares/'+name+'.git':
    run(['git','--git-dir='+str(mirror),'remote','set-url','origin',source],timeout=6)
   else:raise RuntimeError('MIRROR_ORIGIN_MISMATCH')
  run(['git','-c','gc.auto=0','-c','pack.threads=1','--git-dir='+str(mirror),'fetch','--quiet','origin'],timeout=50,github=True)
 h=refs(run(['git','--git-dir='+str(mirror),'show-ref','--heads','--tags'],timeout=15))
 if any(h.get(k)!=v for k,v in s.items()):raise RuntimeError('GITHUB_MOVED_DURING_FETCH')
 try:old=run(['git','--git-dir='+str(mirror),'remote','get-url','forgejo'],timeout=6).strip()
 except RuntimeError:old=''
 if old and old!=target:raise RuntimeError('FORGEJO_REMOTE_MISMATCH')
 if not old:run(['git','--git-dir='+str(mirror),'remote','add','forgejo',target],timeout=6)
 # Atomic local import of only source refs; no force, no delete, no prune.
 specs=[name+':'+name for name in sorted(s)]
 run(['git','-c','gc.auto=0','-c','pack.threads=1','--git-dir='+str(path),'fetch','--atomic','--no-tags',str(mirror)]+specs,timeout=65)
 d2=refs(run(['git','--git-dir='+str(path),'for-each-ref','--format=%(objectname) %(refname)','refs/heads','refs/tags'],timeout=22))
 if any(d2.get(k)!=v for k,v in s.items()):raise RuntimeError('FORGEJO_PARITY_NOT_CONFIRMED')
 return {'state':'SYNCED_FAST_FORWARD_VERIFIED','refs':len(s),'sha':s['refs/heads/main']}

def verify_with_quota_retry(name):
 # One bounded retry for a transient quota failure in the large source repo.
 # Keep the original verify_repo checks, atomic fetch and serial flock.
 try:
  return verify_repo(name)
 except RuntimeError as exc:
  if name!='anthares-kwai-runner' or str(exc)!='HOSTING_PROCESS_LIMIT':
   raise
  time.sleep(4)
  return verify_repo(name)

with open(str(lock),'a+') as f:
 try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except IOError:print('HOSTINGER_GIT_SYNC=ALREADY_RUNNING');sys.exit(0)
 results={n:{'state':status} for n,status in preexisting.items()}
 for n in names:
  try:results[n]=verify_with_quota_retry(n)
  except Exception as e:
   status=str(e)
   if 'TimeoutExpired' in type(e).__name__:status='GIT_TIMEOUT'
   results[n]={'state':'BLOCKED_'+status}
  print(n,results[n]['state'])
 errors=[n for n in names if results[n]['state'].startswith('BLOCKED_')]
 out={'schema':'anthares-hostinger-git-redundancy-v1','checked_utc':datetime.datetime.utcnow().isoformat()+'Z','source':'GitHub','target':'Hostinger Forgejo','results':results,'failures':errors,'no_force':True,'no_prune':True}
 temp=state.with_name(state.name+'.'+str(os.getpid())+'.tmp')
 temp.write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');temp.chmod(0o600);os.replace(str(temp),str(state))
 print('HOSTINGER_GIT_SYNC='+('PARTIAL' if errors else 'VERIFIED'),'covered=',len(names)-len(errors)+len(preexisting),'blocked=',len(errors))
 sys.exit(2 if errors else 0)
