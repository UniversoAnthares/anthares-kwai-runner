$ErrorActionPreference='Stop'
$root='D:\AntharsWork\cortes-social-browser-20261020'
$log=Join-Path $root 'threads-neon-sync-task.log'
try {
 . 'D:\AntharsWork\AntharesRemoteAgent\agent-env.ps1'
 if([string]::IsNullOrWhiteSpace($env:ANTHARES_DEVICE_TOKEN)){throw 'DEVICE_CREDENTIAL_MISSING'}
 $node='C:\Program Files\nodejs\node.exe'
 $sync=Join-Path $root 'threads-neon-sync.mjs'
 $result=@(& $node $sync 2>&1)
 $code=$LASTEXITCODE
 foreach($line in $result){
  $clean=[string]$line
  if($env:ANTHARES_DEVICE_TOKEN){$clean=$clean.Replace($env:ANTHARES_DEVICE_TOKEN,'[REDACTED]')}
  [IO.File]::AppendAllText($log,([DateTime]::UtcNow.ToString('o')+' '+$clean+[Environment]::NewLine))
 }
 exit $code
}catch{
 [IO.File]::AppendAllText($log,([DateTime]::UtcNow.ToString('o')+' SYNC_WRAPPER_FAILURE='+$_.Exception.GetType().Name+[Environment]::NewLine))
 exit 4
}