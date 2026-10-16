param(
  [Parameter(Position=0)][ValidateSet('status','health','devices','backends','recover','start','stop','reset','foreground','launch','identity','ui','lease','release')][string]$Command='status',
  [switch]$AllowBackendReset,
  [string]$Owner='cli',
  [int]$TtlSeconds=120,
  [switch]$Pretty
)
$ErrorActionPreference='Stop'
$runtime='C:\ProgramData\AntharesRemoteAgent\android-runtime\anthares-android-runtime-v2.ps1'
if(-not (Test-Path $runtime)){throw "canonical runtime missing: $runtime"}
function Invoke-Canonical([string]$Cmd,[switch]$Start,[switch]$Reset){
  $args=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$runtime,'-Command',$Cmd,'-Target','memu')
  if($Start){$args+='-AllowBackendStart'}
  if($Reset){$args+='-AllowBackendReset'}
  $raw=& powershell.exe @args | Out-String
  if($LASTEXITCODE -ne 0){throw "canonical runtime exit $LASTEXITCODE"}
  $raw.Trim()|ConvertFrom-Json
}
try{
  switch($Command){
    'status'   {$result=Invoke-Canonical 'health'}
    'health'   {$result=Invoke-Canonical 'health'}
    'devices'  {$h=Invoke-Canonical 'health';$result=[ordered]@{ok=$true;physical=$h.physical;memu=$h.memu;source='canonical_runtime'}}
    'backends' {$h=Invoke-Canonical 'health';$result=[ordered]@{ok=$true;memu=$h.memu;source='canonical_runtime'}}
    'recover'  {$result=Invoke-Canonical 'recover' -Start -Reset:$AllowBackendReset}
    'start'    {$result=Invoke-Canonical 'recover' -Start}
    'foreground' {$result=Invoke-Canonical 'foreground'}
    'launch'   {$result=Invoke-Canonical 'launch'}
    'identity' {$result=Invoke-Canonical 'identity'}
    'ui'       {$result=Invoke-Canonical 'ui'}
    'stop'     {$result=[ordered]@{ok=$false;failure_class='DEPRECATED_SECOND_AUTHORITY';reason='stop is not exposed through legacy CLI; SYSTEM runtime remains sole authority'}}
    'reset'    {$result=Invoke-Canonical 'recover' -Start -Reset}
    'lease'    {$result=[ordered]@{ok=$true;lease_mode='runtime_mutex';owner=$Owner;ttl_seconds=$TtlSeconds;note='MEmu recovery authority is serialized by canonical runtime mutex'}}
    'release'  {$result=[ordered]@{ok=$true;lease_mode='runtime_mutex';owner=$Owner;note='no independent legacy lease authority remains'}}
  }
  if($Pretty){$result|ConvertTo-Json -Depth 12}else{$result|ConvertTo-Json -Depth 12 -Compress}
  if($result.PSObject.Properties.Name -contains 'ok' -and -not $result.ok){exit 2}
  exit 0
}catch{
  [ordered]@{ok=$false;failure_class='ANTHARES_COMPONENT_FAILURE';error=$_.Exception.Message}|ConvertTo-Json -Compress
  exit 3
}