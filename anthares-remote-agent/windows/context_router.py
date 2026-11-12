"""Owner-context ARA CLI broker. No credentials are read or copied by this module."""
import argparse,base64,ctypes,hashlib,json,os,pathlib,re,subprocess,sys,time,uuid
ROOT=pathlib.Path(__file__).resolve().parent
def config():
    return json.loads((ROOT/'config.json').read_text(encoding='utf-8-sig'))
def policy(c):
    b=pathlib.Path(c['governance_root']);m=json.loads((b/'manifest.json').read_text())
    for name in ('REGRAS-OBRIGATORIAS.md','INDICE.md','PROMPT-MESTRE.md'):
        if hashlib.sha256((b/name).read_bytes()).hexdigest()!=m['files'][name]:
            raise RuntimeError('GOVERNANCE_INTEGRITY_FAILURE')
    return m['version']
def sid():
    import win32api,win32con,win32security
    t=win32security.OpenProcessToken(win32api.GetCurrentProcess(),win32con.TOKEN_QUERY)
    try:return win32security.ConvertSidToStringSid(win32security.GetTokenInformation(t,win32security.TokenUser)[0])
    finally:t.Close()
def audit(c,r,status):
    row=dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),id=r.get('id'),service=r.get('service'),status=status,pid=os.getpid(),identity_sid=sid(),governance=policy(c))
    with (ROOT/'audit.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
def redact(s):
    s=re.sub(r'(?i)\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b','[REDACTED]',s)
    s=re.sub(r'(?i)(bearer\s+|(?:api[_-]?key|access[_-]?token|refresh[_-]?token|oauth[_-]?token|password|authorization|token|secret)\s*[:=]\s*)\S+',r'\1[REDACTED]',s)
    return s[:60000]
def validate(r):
    if not re.fullmatch('[a-f0-9]{32}',r.get('id','')):raise ValueError('REQUEST_ID_REJECTED')
    a=r.get('arguments')
    if not isinstance(a,list) or not 1<=len(a)<=80 or any(not isinstance(v,str) or len(v)>4096 or any(x in v for x in '\x00\r\n') for v in a):
        raise ValueError('ARGUMENTS_REJECTED')
    if type(r.get('timeout')) is not int or not 5<=r['timeout']<=120:raise ValueError('TIMEOUT_REJECTED')
    return a
def cli(argv,cwd,deadline):
    left=deadline-time.monotonic()
    if left<=0:raise TimeoutError('DEADLINE_REACHED')
    env=os.environ.copy()
    for k in list(env):
        if k.startswith(('CLOUDFLARE_','CF_API_','GH_TOKEN','GITHUB_TOKEN','ANTHARES_DEVICE_')) or k=='GH_DEBUG':
            env.pop(k,None)
    env.update(CI='true',WRANGLER_SEND_METRICS='false',WRANGLER_LOG_LEVEL='error')
    child=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        out,err=child.communicate(timeout=left)
        return child.returncode,(out+err).decode('utf-8',errors='replace')
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW,timeout=5)
        child.kill();child.communicate(timeout=3)
        raise TimeoutError('TIMED_OUT_RECONCILE_REQUIRED')
def execute(c,r):
    a=validate(r);service=r['service'];deadline=time.monotonic()+r['timeout']
    if service=='Windows':
        if a!=['identity']:raise ValueError('WINDOWS_OPERATION_UNREGISTERED')
        return dict(ok=True,status='COMPLETED',context=service,sid=sid(),identity=os.environ.get('USERNAME'))
    if sid()!=c['user_sid']:raise ValueError('WRONG_WINDOWS_IDENTITY')
    cwd=r.get('cwd') or str(ROOT)
    if cwd.startswith('\\\\') or not pathlib.Path(cwd).is_dir():raise ValueError('WORKING_DIRECTORY_REJECTED')
    if service=='Cloudflare':
        if a[0] in ('login','logout','init') or any(re.match(r'^--(debug|log-level)(=|$)',v) for v in a):raise ValueError('INTERACTIVE_OR_DIAGNOSTIC_OPERATION_REJECTED')
        code,text=cli([c['node'],c['wrangler'],'whoami'],cwd,min(deadline,time.monotonic()+20))
        if code or c['cloudflare_account'] not in text:raise ValueError('PROVIDER_IDENTITY_NOT_VERIFIED')
        if a==['whoami']:return dict(ok=True,status='COMPLETED',output='CLOUDFLARE_ACCOUNT_VERIFIED='+c['cloudflare_account'])
        command=[c['node'],c['wrangler']]+a
    elif service=='GitHub':
        if not c.get('github_enabled'):raise ValueError('GITHUB_ROUTE_DISABLED')
        if a[0] in ('auth','alias','extension') or any(re.match(r'^--(show-token|debug)(=|$)',v) for v in a):raise ValueError('CREDENTIAL_OR_EXTENSION_OPERATION_REJECTED')
        code,text=cli([c['gh'],'api','user','--jq','.login'],cwd,min(deadline,time.monotonic()+20))
        if code or text.strip()!=c['github_account']:raise ValueError('PROVIDER_IDENTITY_NOT_VERIFIED')
        if a==['api','user','--jq','.login']:return dict(ok=True,status='COMPLETED',output=text.strip())
        command=[c['gh']]+a
    elif service=='Hostinger':
        if a not in (['identity'],['listener-status']):raise ValueError('HOSTINGER_READONLY_OPERATION_UNREGISTERED')
        remote="import os,json;print(json.dumps({'operation':'identity','uid':os.geteuid(),'credential_read':False}))"
        if a==['listener-status']:
            remote="import pathlib,json,os,stat\np=pathlib.Path.home()/'domains/anthares.us/.anthares-ara-notify/listener.token'\nr={'operation':'listener-status','exists':p.exists(),'credential_read':False}\nif p.exists():\n s=p.lstat();r.update(regular_file=stat.S_ISREG(s.st_mode),symlink=p.is_symlink(),nonempty=s.st_size>0,owner_matches_executor=s.st_uid==os.geteuid(),group_or_other_access=bool(s.st_mode & 0o077))\nprint(json.dumps(r))"
        encoded=base64.b64encode(remote.encode()).decode()
        remote_command="/opt/alt/python311/bin/python3.11 -c 'exec(__import__(\"base64\").b64decode(\""+encoded+"\"))'"
        command=[c['ssh'],'-F',c['ssh_config'],'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=7',c['hostinger_alias'],remote_command]
    elif service=='Lifecycle' and a==['stop']:return dict(ok=True,status='STOPPED')
    else:raise ValueError('SERVICE_UNREGISTERED')
    code,text=cli(command,cwd,deadline)
    return dict(ok=code==0,status='COMPLETED',exit_code=code,output=redact(text))
def pipe_io(h,data=None,timeout=5):
    import win32event,win32file,winerror,pywintypes
    ov=pywintypes.OVERLAPPED();ov.hEvent=win32event.CreateEvent(None,True,False,'AntharesContextIO-'+uuid.uuid4().hex)
    try:
        if data is None:err,buf=win32file.ReadFile(h,65536,ov)
        else:err,n=win32file.WriteFile(h,data,ov)
        if err==winerror.ERROR_IO_PENDING:
            if win32event.WaitForSingleObject(ov.hEvent,int(timeout*1000))!=win32event.WAIT_OBJECT_0:
                win32file.CancelIoEx(h,ov);raise TimeoutError('PIPE_IO_TIMEOUT')
        n=win32file.GetOverlappedResult(h,ov,True)
        return bytes(buf[:n]) if data is None else None
    finally:ov.hEvent.Close()
def serve(c):
    import win32api,win32con,win32event,win32file,win32job,win32pipe,win32security,winerror,pywintypes
    if sid()!=c['user_sid']:raise RuntimeError('SERVER_REQUIRES_REGISTERED_USER')
    policy(c)
    # A nested owned Job Object prevents descendant processes surviving this request.
    job=win32job.CreateJobObject(None,'AntharesContextJob-'+uuid.uuid4().hex)
    info=win32job.QueryInformationJobObject(job,win32job.JobObjectExtendedLimitInformation)
    info['BasicLimitInformation']['LimitFlags']|=win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job,win32job.JobObjectExtendedLimitInformation,info)
    win32job.AssignProcessToJobObject(job,win32api.GetCurrentProcess())
    sa=pywintypes.SECURITY_ATTRIBUTES()
    sa.SECURITY_DESCRIPTOR=win32security.ConvertStringSecurityDescriptorToSecurityDescriptor('D:P(A;;GA;;;SY)(A;;GA;;;'+c['user_sid']+')',1)
    h=win32pipe.CreateNamedPipe('\\\\.\\pipe\\'+c['pipe'],win32pipe.PIPE_ACCESS_DUPLEX|win32file.FILE_FLAG_OVERLAPPED|0x00080000,win32pipe.PIPE_TYPE_MESSAGE|win32pipe.PIPE_READMODE_MESSAGE|win32pipe.PIPE_WAIT|0x8,1,65536,65536,0,sa)
    try:
        ov=pywintypes.OVERLAPPED();ov.hEvent=win32event.CreateEvent(None,True,False,'AntharesContextIO-'+uuid.uuid4().hex)
        try:
            try:win32pipe.ConnectNamedPipe(h,ov)
            except pywintypes.error as e:
                if e.winerror!=winerror.ERROR_PIPE_CONNECTED:raise
                win32event.SetEvent(ov.hEvent)
            win32event.WaitForSingleObject(ov.hEvent,win32event.INFINITE)
        finally:ov.hEvent.Close()
        r=json.loads(pipe_io(h,timeout=5))
        try:
            validate(r)
            seen=set()
            for line in (ROOT/'audit.jsonl').read_text(encoding='utf-8-sig').splitlines():
                if line:seen.add(json.loads(line).get('id'))
            if r['id'] in seen:raise ValueError('DUPLICATE_REQUEST_RECONCILE_REQUIRED')
            audit(c,r,'STARTED')
            try:result=execute(c,r)
            except TimeoutError:result=dict(ok=False,status='TIMED_OUT_RECONCILE_REQUIRED',error='TIMED_OUT_RECONCILE_REQUIRED')
            except Exception as e:result=dict(ok=False,status='REJECTED',error=str(e))
            result.update(request_id=r['id'],context=r['service'],sid=sid(),identity=os.environ.get('USERNAME'))
            audit(c,r,result['status'])
        except Exception as e:result=dict(ok=False,status='REJECTED',error=str(e))
        pipe_io(h,json.dumps(result).encode(),timeout=3)
        try:pipe_io(h,timeout=3)
        except Exception:pass
    finally:
        h.Close()
        # Keep the owned job handle alive until process exit; closing it kills only owned descendants.
        globals()['_owned_job']=job
def request(c,r):
    import win32api,win32con,win32file,win32pipe,win32security,pywintypes
    policy(c);validate(r)
    if r['service']=='Windows':return execute(c,r)
    h=None
    for attempt in range(8):
        if attempt in (0,3,6):
            subprocess.run(['schtasks','/Run','/TN','Anthares Context Router User'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW,timeout=5)
        try:
            h=win32file.CreateFile('\\\\.\\pipe\\'+c['pipe'],win32con.GENERIC_READ|win32con.GENERIC_WRITE,0,None,win32con.OPEN_EXISTING,win32file.FILE_FLAG_OVERLAPPED,None);break
        except pywintypes.error as e:
            if e.winerror not in (2,231):raise
            try:win32pipe.WaitNamedPipe('\\\\.\\pipe\\'+c['pipe'],1000)
            except pywintypes.error:time.sleep(0.2)
    if h is None:raise RuntimeError('USER_CONTEXT_UNAVAILABLE_NOT_SUBMITTED')
    try:
        # Validate the server's Windows identity before transmitting any request.
        k=ctypes.WinDLL('kernel32',use_last_error=True);pid=ctypes.c_ulong()
        if not k.GetNamedPipeServerProcessId(ctypes.c_void_p(int(h)),ctypes.byref(pid)):raise RuntimeError('SERVER_IDENTITY_UNAVAILABLE')
        proc=win32api.OpenProcess(0x1000,False,pid.value)
        try:
            token=win32security.OpenProcessToken(proc,win32con.TOKEN_QUERY)
            try:owner=win32security.ConvertSidToStringSid(win32security.GetTokenInformation(token,win32security.TokenUser)[0])
            finally:token.Close()
        finally:proc.Close()
        if owner!=c['user_sid']:raise RuntimeError('SERVER_IDENTITY_REJECTED')
        win32pipe.SetNamedPipeHandleState(h,win32pipe.PIPE_READMODE_MESSAGE,None,None)
        pipe_io(h,json.dumps(r).encode(),timeout=3)
        result=json.loads(pipe_io(h,timeout=r['timeout']+8))
        pipe_io(h,b'ACK',timeout=2)
        return result
    finally:h.Close()
def main():
    p=argparse.ArgumentParser();p.add_argument('--serve',action='store_true');p.add_argument('--request-b64');p.add_argument('--service',default='Windows');p.add_argument('--arguments-b64',default='WyJpZGVudGl0eSJd');p.add_argument('--cwd',default='');p.add_argument('--timeout',type=int,default=45);p.add_argument('--id',default=uuid.uuid4().hex)
    a=p.parse_args();c=config()
    if a.serve:serve(c);return
    r=json.loads(base64.b64decode(a.request_b64)) if a.request_b64 else dict(id=a.id,service=a.service,arguments=json.loads(base64.b64decode(a.arguments_b64)),cwd=a.cwd,timeout=a.timeout)
    try:result=request(c,r)
    except Exception as e:result=dict(ok=False,status='NOT_SUBMITTED_OR_RECONCILE_REQUIRED',error=redact(str(e)),request_id=a.id)
    print(json.dumps(result),flush=True)
if __name__=='__main__':main()
