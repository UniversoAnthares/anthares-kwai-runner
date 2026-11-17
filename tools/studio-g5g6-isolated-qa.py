#!/usr/bin/env python3
"""One-time G5/G6 isolated WordPress QA using existing Hostinger checkout and authenticated CI SSH."""
import json,os,pathlib,socket,subprocess,tempfile,urllib.request
HOST_KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIA7FQ2RBq0cii+VVCqcB90JxkJRPdurdrX1RGThhKtT2'
def bridge(token):
    req=urllib.request.Request('https://gitlab.com/api/v4/projects/87361776/variables?per_page=100',
        headers={'PRIVATE-TOKEN':token,'User-Agent':'anthares-studio-g5-isolated-qa'})
    with urllib.request.urlopen(req,timeout=20) as r:
        rows=json.load(r)
    v={i.get('key'):i.get('value') for i in rows}
    needed=('ANTHARES_QA_SSH_KEY','ANTHARES_QA_SSH_HOST','ANTHARES_QA_SSH_USER')
    if any(not v.get(x) for x in needed):raise RuntimeError('SSH_BRIDGE_MISSING')
    host=v['ANTHARES_QA_SSH_HOST'];user=v['ANTHARES_QA_SSH_USER']
    port=str(v.get('ANTHARES_QA_SSH_PORT') or '65002')
    if user!='u566597497' or port!='65002':raise RuntimeError('SSH_TARGET_MISMATCH')
    if {r[4][0] for r in socket.getaddrinfo(host,None,family=socket.AF_INET)}!={'195.35.39.110'}:
        raise RuntimeError('SSH_IP_MISMATCH')
    return v['ANTHARES_QA_SSH_KEY'],host,port,user

REMOTE=r"""
import os,pathlib,shutil,subprocess,tempfile,sys,re
home=pathlib.Path.home()
private=home/'domains/anthares.us/anthares-private-storage'
source=private/'studio-g6-review-20261116'
expected='3efad7ad3b41e765132f625202daad88f8f2ee7d'
def require(condition,code):
 if not condition:raise RuntimeError(code)
require(private.is_dir() and (source/'.git').is_dir(),'G6_CHECKOUT_MISSING')
head=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,timeout=10).strip()
require(head==expected,'G6_CHECKOUT_CHANGED')
print('G6_SOURCE_HEAD_PROVEN='+head,flush=True)
temp=pathlib.Path(tempfile.mkdtemp(prefix='studio-g5g6-qa-',dir=private))
try:
 repo=temp/'code'
 cp=subprocess.run(['git','clone','--quiet','--no-hardlinks','--local',str(source),str(repo)],
                   capture_output=True,text=True,timeout=35)
 require(cp.returncode==0,'CLEAN_CHECKOUT_FAILED')
 checkout=subprocess.run(['git','-C',str(repo),'checkout','--quiet','--detach',head],capture_output=True,text=True,timeout=10)
 require(checkout.returncode==0,'G6_CHECKOUT_DETACH_FAILED')
 check=subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
 require(not check,'TEST_COPY_DIRTY')
 p=subprocess.run(['/opt/alt/php83/usr/bin/php','-l',str(repo/'anthares-studio/anthares-estudio.php')],
                  capture_output=True,text=True,timeout=15)
 require(p.returncode==0,'G6_PHP_LINT_FAILED')
 print('G6_PHP_LINT=PASS',flush=True)
 q=subprocess.run(['/opt/alt/python311/bin/python3.11','-m','unittest','discover','-s',str(repo/'anthares-studio/tests'),'-p','test*.py'],
                  cwd=repo,capture_output=True,text=True,timeout=75)
 if q.returncode!=0:
  print('G6_UNIT_TEST_FAILED_COUNT='+str(len(re.findall('FAIL|ERROR',q.stderr))),flush=True)
 require(q.returncode==0,'G6_UNIT_TEST_FAILED')
 count=re.search(r'Ran (\d+) tests',q.stderr)
 print('G6_UNIT_TESTS_PASS='+str(count.group(1) if count else 'UNKNOWN'),flush=True)
 coverage=subprocess.run(['/opt/alt/python311/bin/python3.11','qa/manifest-coverage-preflight.py','--check'],
                         cwd=repo,capture_output=True,text=True,timeout=45)
 require(coverage.returncode==0,'G6_QA_MANIFEST_FAIL')
 line=next((x for x in coverage.stdout.splitlines() if 'QA_MANIFEST' in x or 'auditable=' in x),'PASS')
 print('G6_MANIFEST='+re.sub(r'[^A-Za-z0-9 _=/.-]','',line)[:150],flush=True)
 g5=repo/'anthares-studio/tests/integration/g5-runtime-isolated.sh'
 require(g5.is_file(),'G5_ISOLATED_SCRIPT_NOT_FOUND')
 print('G5_ISOLATED_RUN_STARTED=1',flush=True)
 try:
  run=subprocess.run(['bash',str(g5)],cwd=repo,capture_output=True,text=True,timeout=260)
 except subprocess.TimeoutExpired:
  raise RuntimeError('G5_ISOLATED_TIMEOUT')
 for line in run.stdout.splitlines():
  if line.startswith(('G5_','SOURCE_COUNT=','REFERENCE_ERRORS=','SUCCESS:','Error:')):
   clean=re.sub(r'[^A-Za-z0-9 _=:/.-]','_',line)[:180]
   print('G5_QA_EVENT='+clean,flush=True)
 if run.returncode:
  reason=(run.stderr.strip().splitlines() or run.stdout.strip().splitlines() or ['UNKNOWN'])[-1]
  clean=re.sub(r'[^A-Za-z0-9 _=:/.-]','_',reason)[:120]
  print('G5_FAILURE_KIND='+clean,flush=True)
 require(run.returncode==0,'G5_RUNTIME_ISOLATED_FAILED')
 require('G5_ACF_RUNTIME_INTEGRATION_PASS' in run.stdout,'G5_MISSING_SUCCESS')
 print('G5_ACF_RUNTIME_INTEGRATION_PASS=1',flush=True)
 print('G5_G6_GATES_ISOLATED_PROVEN=1',flush=True)
finally:
 shutil.rmtree(temp,ignore_errors=True)
 print('G5_QA_TEMP_CLEANUP=1',flush=True)
"""
def main():
    if os.getenv('GITHUB_REF')!='refs/heads/coord/studio-g4-g5-20261116':raise RuntimeError('WRONG_BRANCH')
    if os.getenv('GITHUB_EVENT_NAME')!='push':raise RuntimeError('WRONG_EVENT')
    token=os.getenv('GITLAB_TOKEN')
    if not token:raise RuntimeError('PROTECTED_BRIDGE_TOKEN_MISSING')
    key,host,port,user=bridge(token)
    with tempfile.TemporaryDirectory(prefix='studio-g5-isolated-') as tmp:
        keyp=pathlib.Path(tmp)/'key';keyp.write_text(key);keyp.chmod(0o600)
        known=pathlib.Path(tmp)/'hosts';known.write_text('anthares-g5qa '+HOST_KEY+'\n');known.chmod(0o600)
        cmd=['ssh','-T','-i',str(keyp),'-p',port,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
             '-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
             '-o','UserKnownHostsFile='+str(known),'-o','HostKeyAlias=anthares-g5qa',
             f'{user}@{host}','/opt/alt/python311/bin/python3.11 -']
        r=subprocess.run(cmd,input=REMOTE,text=True,capture_output=True,timeout=310)
        for line in r.stdout.splitlines():
            if line.startswith(('G5_','G6_')):print(line,flush=True)
        if r.returncode:
            tail=(r.stderr.strip().splitlines() or ['UNCLASSIFIED'])[-1]
            tail=''.join(c if c.isalnum() or c in ' _:.-=' else '_' for c in tail)[:150]
            print('G5_QA_REMOTE_ERROR='+tail,flush=True)
            raise RuntimeError('G5_QA_FAILED')
        if 'G5_G6_GATES_ISOLATED_PROVEN=1' not in r.stdout:raise RuntimeError('G5_RESULT_MISSING')
if __name__=='__main__':
    main()
