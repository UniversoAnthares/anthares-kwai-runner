[CmdletBinding()]
param(
 [ValidateSet('Invoke','Serve','Stop')][string]$Mode='Invoke',
 [ValidateSet('Windows','Cloudflare','GitHub')][string]$Service='Windows',
 [string]$ArgumentsJson='["identity"]',
 [string]$WorkingDirectory='',
 [ValidateRange(5,120)][int]$TimeoutSeconds=45,
 [string]$RequestId=([guid]::NewGuid().ToString('N'))
)
$ErrorActionPreference='Stop'
$cfg=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'config.json') -Raw | ConvertFrom-Json
$pipeName=$cfg.pipe
function Assert-OwnerPolicy {
 $m=Get-Content -LiteralPath (Join-Path $cfg.governance_root 'manifest.json') -Raw|ConvertFrom-Json
 foreach($name in @('REGRAS-OBRIGATORIAS.md','INDICE.md','PROMPT-MESTRE.md')){
  $path=Join-Path $cfg.governance_root $name
  $hasher=[Security.Cryptography.SHA256]::Create()
  try{$digest=[BitConverter]::ToString($hasher.ComputeHash([IO.File]::ReadAllBytes($path))).Replace('-','').ToLowerInvariant()}finally{$hasher.Dispose()}
  if($digest -ne $m.files.$name){throw 'GOVERNANCE_INTEGRITY_FAILURE'}
 }
 $cfg.governance=$m.version
}
Assert-OwnerPolicy
function Invoke-RegisteredTool($request) {
 Assert-OwnerPolicy
 $argsList=@($request.arguments)
 if($request.service -eq 'GitHub' -and -not $cfg.github_enabled){throw 'GITHUB_CREDENTIAL_RENEWAL_REQUIRED'}
 if($argsList.Count -lt 1 -or $argsList.Count -gt 80){throw 'ARGUMENTS_REJECTED'}
 foreach($a in $argsList){if($a -isnot [string] -or $a.Length -gt 4096 -or $a.Contains([char]0) -or $a.Contains("`r") -or $a.Contains("`n")){throw 'ARGUMENTS_REJECTED'}}
 if($request.service -eq 'Windows'){
  if($argsList.Count -ne 1 -or $argsList[0] -ne 'identity'){throw 'WINDOWS_OPERATION_UNREGISTERED'}
  return @{ok=$true;status='COMPLETED';identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value;context='Windows';request_id=$request.id}
 }
 if([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne $cfg.user_sid){throw 'WRONG_WINDOWS_IDENTITY'}
 if($request.service -eq 'Cloudflare'){
  $file=$cfg.node;$prefix=@($cfg.wrangler)
  if(($argsList[0] -in @('login','logout','init')) -or (@($argsList | Where-Object {$_ -match '^--(debug|log-level)(=|$)'}).Count -gt 0)){throw 'INTERACTIVE_OR_DIAGNOSTIC_OPERATION_REJECTED'}
 }elseif($request.service -eq 'GitHub'){
  $file=$cfg.gh;$prefix=@()
  if(($argsList[0] -in @('extension','alias','auth')) -or (@($argsList | Where-Object {$_ -match '^--(show-token|debug)(=|$)'}).Count -gt 0)){throw 'CREDENTIAL_OR_EXTENSION_OPERATION_REJECTED'}
 }else{throw 'SERVICE_UNREGISTERED'}
 if(-not (Test-Path -LiteralPath $file -PathType Leaf)){throw 'TOOL_UNAVAILABLE'}
 $cwd=$request.cwd
 if(-not $cwd){$cwd=$PSScriptRoot}
 $cwd=[IO.Path]::GetFullPath($cwd)
 if($cwd.StartsWith('\\') -or -not (Test-Path -LiteralPath $cwd -PathType Container)){throw 'WORKING_DIRECTORY_REJECTED'}
 # Use a literal argv array encoded as JSON, never concatenate a shell command.
 $payload=@{file=$file;arguments=@($prefix)+$argsList;cwd=$cwd;timeout=[int]$request.timeout;service=$request.service;expected_account=$cfg.cloudflare_account;expected_github=$cfg.github_account}
 $json=$payload|ConvertTo-Json -Compress -Depth 5
 $python=@'
import sys,json,subprocess,os,re
p=json.loads(sys.stdin.read())
env=os.environ.copy()
for k in list(env):
 if k.startswith(('CLOUDFLARE_','CF_API_','GH_TOKEN','GITHUB_TOKEN','ANTHARES_DEVICE_')):
  env.pop(k,None)
env.pop('GH_DEBUG',None)
env.update(CI='true',WRANGLER_SEND_METRICS='false',WRANGLER_LOG_LEVEL='error')
si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
child=None
try:
 if p['service']=='Cloudflare':
  probe=subprocess.run([p['file'],p['arguments'][0],'whoami'],cwd=p['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW,startupinfo=si,timeout=20)
  if probe.returncode or p['expected_account'] not in (probe.stdout+probe.stderr).decode('utf-8',errors='replace'):
   print(json.dumps(dict(exit_code=401,output='PROVIDER_IDENTITY_NOT_VERIFIED; authenticate existing owner account; do not switch identity or copy credentials',timed_out=False)))
   sys.exit(0)
  if p['arguments'][1:]==['whoami']:
   print(json.dumps(dict(exit_code=0,output='CLOUDFLARE_ACCOUNT_VERIFIED='+p['expected_account'],timed_out=False)))
   sys.exit(0)
 if p['service']=='GitHub':
  probe=subprocess.run([p['file'],'api','user','--jq','.login'],cwd=p['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW,startupinfo=si,timeout=20)
  if probe.returncode or probe.stdout.decode('utf-8',errors='replace').strip()!=p['expected_github']:
   print(json.dumps(dict(exit_code=401,output='PROVIDER_IDENTITY_NOT_VERIFIED; authenticate existing owner account; do not switch identity or copy credentials',timed_out=False)))
   sys.exit(0)
 child=subprocess.Popen([p['file']]+p['arguments'],cwd=p['cwd'],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW,startupinfo=si)
 try:
  out,err=child.communicate(timeout=p['timeout'])
  text=(out+err).decode('utf-8',errors='replace')
  text=re.sub(r'(?i)(bearer\s+|(?:api[_-]?key|access[_-]?token|refresh[_-]?token|oauth[_-]?token|password|authorization)\s*[:=]\s*)\S+',r'\1[REDACTED]',text)
  text=re.sub(r'(?i)\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b','[REDACTED]',text)
  text=re.sub(r'(?i)((?:token|secret)\s*:\s*)\S+',r'\1[REDACTED]',text)
  print(json.dumps(dict(exit_code=child.returncode,output=text[:60000],timed_out=False)))
 except subprocess.TimeoutExpired:
  subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
  child.communicate(timeout=5)
  print(json.dumps(dict(exit_code=None,output='',timed_out=True)))
finally:
 if child and child.poll() is None:
  subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
'@
 $encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($python))
 $psi=New-Object Diagnostics.ProcessStartInfo
 $psi.FileName=$cfg.python
 $psi.Arguments='-B -c "import base64;exec(base64.b64decode('+"'"+$encoded+"'"+'))"'
 $psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
 $psi.RedirectStandardInput=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
 $proc=New-Object Diagnostics.Process;$proc.StartInfo=$psi
 try{
  [void]$proc.Start()
  $proc.StandardInput.Write($json);$proc.StandardInput.Close()
  $outTask=$proc.StandardOutput.ReadLineAsync();$errTask=$proc.StandardError.ReadToEndAsync()
  if(-not $proc.WaitForExit(([int]$request.timeout+12)*1000)){throw 'CHILD_STATE_UNCERTAIN'}
  if(-not $outTask.Wait(2000)){throw 'CHILD_RESULT_UNAVAILABLE'}
  $result=$outTask.Result|ConvertFrom-Json
  if($null -eq $result){throw 'CHILD_RESULT_UNAVAILABLE'}
  return @{ok=($result.exit_code -eq 0 -and -not $result.timed_out);status=$(if($result.timed_out){'TIMED_OUT_RECONCILE_REQUIRED'}else{'COMPLETED'});exit_code=$result.exit_code;output=$result.output;identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;sid=$cfg.user_sid;context=$request.service;request_id=$request.id}
 }finally{if($proc.Id -and -not $proc.HasExited){& taskkill.exe /PID $proc.Id /T /F 2>$null|Out-Null};$proc.Dispose()}
}
function Write-Audit($request,$status){
 $record=@{utc=[DateTimeOffset]::UtcNow.ToString('o');id=$request.id;service=$request.service;status=$status;pid=$PID;identity_sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value;governance=$cfg.governance}
 # Metadata only: never persist command arguments, provider output or credentials.
 ($record|ConvertTo-Json -Compress)|Add-Content -LiteralPath (Join-Path $PSScriptRoot 'audit.jsonl') -Encoding UTF8
}
if($Mode -eq 'Serve'){
 if([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne $cfg.user_sid){throw 'SERVER_REQUIRES_REGISTERED_USER'}
 $seen=@{}
 foreach($line in [IO.File]::ReadLines((Join-Path $PSScriptRoot 'audit.jsonl'))){try{$prior=$line|ConvertFrom-Json;if($prior.id){$seen[$prior.id]=$true}}catch{throw 'REQUEST_LEDGER_CORRUPT'}}
 while($true){
  $pipe=$null;$reader=$null;$writer=$null
  try{
   $security=New-Object IO.Pipes.PipeSecurity
   foreach($sid in @('S-1-5-18',$cfg.user_sid)){
    $rule=New-Object IO.Pipes.PipeAccessRule((New-Object Security.Principal.SecurityIdentifier($sid)),[IO.Pipes.PipeAccessRights]::FullControl,[Security.AccessControl.AccessControlType]::Allow)
    $security.AddAccessRule($rule)
   }
   $security.SetAccessRuleProtection($true,$false)
   $pipe=New-Object IO.Pipes.NamedPipeServerStream($pipeName,[IO.Pipes.PipeDirection]::InOut,1,[IO.Pipes.PipeTransmissionMode]::Byte,[IO.Pipes.PipeOptions]::Asynchronous,65536,65536,$security)
   $pipe.WaitForConnection()
   $reader=New-Object IO.StreamReader($pipe,(New-Object Text.UTF8Encoding($false)),$false,4096,$true)
   $writer=New-Object IO.StreamWriter($pipe,(New-Object Text.UTF8Encoding($false)),4096,$true);$writer.AutoFlush=$true
   $read=$reader.ReadLineAsync()
   if(-not $read.Wait(5000)){throw 'REQUEST_READ_TIMEOUT'}
   if($read.Result.Length -gt 32768){throw 'REQUEST_TOO_LARGE'}
   $req=$read.Result|ConvertFrom-Json
   if($req.id -notmatch '^[a-f0-9]{32}$' -or $req.timeout -lt 5 -or $req.timeout -gt 120){throw 'REQUEST_REJECTED'}
   if($seen.ContainsKey($req.id)){throw 'DUPLICATE_REQUEST_RECONCILE_REQUIRED'}
   $seen[$req.id]=$true
   Write-Audit $req 'STARTED'
   if($req.service -eq 'Lifecycle' -and $req.arguments[0] -eq 'stop'){$response=@{ok=$true;status='STOPPED'};$stopping=$true}else{$stopping=$false}
   try{if(-not $stopping){$response=Invoke-RegisteredTool $req}}catch{$response=@{ok=$false;status='REJECTED';error=$_.Exception.Message;request_id=$req.id}}
   Write-Audit $req $response.status
   $writer.WriteLine(($response|ConvertTo-Json -Compress -Depth 6))
   if($stopping){break}
  }catch{
   if($writer){try{$writer.WriteLine((@{ok=$false;status='REJECTED';error=$_.Exception.Message}|ConvertTo-Json -Compress))}catch{}}
  }finally{
   if($writer){$writer.Dispose()};if($reader){$reader.Dispose()};if($pipe){$pipe.Dispose()}
  }
 }
}else{
 $argsList=ConvertFrom-Json -InputObject $ArgumentsJson
 $req=@{id=$RequestId;service=$Service;arguments=@($argsList);cwd=$WorkingDirectory;timeout=$TimeoutSeconds}
 if($Mode -eq 'Stop'){$req.service='Lifecycle';$req.arguments=@('stop')}
 if($Service -eq 'Windows' -and $Mode -ne 'Stop'){
  Invoke-RegisteredTool $req|ConvertTo-Json -Compress -Depth 6
  exit
 }
 $pipe=New-Object IO.Pipes.NamedPipeClientStream('.',$pipeName,[IO.Pipes.PipeDirection]::InOut,[IO.Pipes.PipeOptions]::Asynchronous)
 $reader=$null;$writer=$null
 try{
  try{$pipe.Connect(3000)}catch{throw 'USER_CONTEXT_UNAVAILABLE: registered user must be logged on; do not copy credentials or retry through SYSTEM'}
  $reader=New-Object IO.StreamReader($pipe,(New-Object Text.UTF8Encoding($false)),$false,4096,$true)
  $writer=New-Object IO.StreamWriter($pipe,(New-Object Text.UTF8Encoding($false)),4096,$true);$writer.AutoFlush=$true
  $writer.WriteLine(($req|ConvertTo-Json -Compress -Depth 5))
  $read=$reader.ReadLineAsync()
  if(-not $read.Wait(($TimeoutSeconds+20)*1000)){throw 'RESULT_UNCERTAIN: do not resend; reconcile request id'}
  if(-not $read.Result){throw 'RESULT_UNCERTAIN: empty broker response'}
  $read.Result
 }finally{if($writer){$writer.Dispose()};if($reader){$reader.Dispose()};$pipe.Dispose()}
}
