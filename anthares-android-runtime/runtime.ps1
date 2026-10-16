param(
  [ValidateSet('status','health','devices','recover','packages','foreground','launch','identity-probe')][string]$Action='status',
  [string]$Package=''
)
$ErrorActionPreference='Stop'
$canonical='C:\ProgramData\AntharesRemoteAgent\android-runtime\anthares-android-runtime-v2.ps1'
if(-not (Test-Path $canonical)){throw "canonical Anthares Android Runtime missing: $canonical"}
function Invoke-Canonical([string]$Command,[switch]$AllowStart,[switch]$AllowReset){
  $args=@('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$canonical,'-Command',$Command,'-Target','memu')
  if($AllowStart){$args+='-AllowBackendStart'}
  if($AllowReset){$args+='-AllowBackendReset'}
  $raw=& powershell.exe @args | Out-String
  if($LASTEXITCODE -ne 0){throw "canonical runtime exit $LASTEXITCODE"}
  $raw.Trim() | ConvertFrom-Json
}
switch($Action){
  'status' {$out=Invoke-Canonical 'health'}
  'health' {$out=Invoke-Canonical 'health'}
  'devices' {
    $h=Invoke-Canonical 'health'
    $out=[ordered]@{ok=$true;source='canonical_runtime';physical=$h.physical;memu=$h.memu}
  }
  'recover' {$out=Invoke-Canonical 'recover' -AllowStart}
  'foreground' {$out=Invoke-Canonical 'foreground'}
  'launch' {
    if($Package -and $Package -ne 'com.kwai.video'){$out=[ordered]@{ok=$false;reason='legacy_arbitrary_package_launch_retired';canonical_package='com.kwai.video'}}
    else{$out=Invoke-Canonical 'launch'}
  }
  'identity-probe' {$out=Invoke-Canonical 'identity'}
  'packages' {
    $h=Invoke-Canonical 'health'
    $out=[ordered]@{ok=$true;source='canonical_runtime';reason='legacy_package_enumeration_retired';kwai_package=$h.memu.kwai_package;package_installed=$h.memu.package_installed;health=$h.memu}
  }
}
$out | ConvertTo-Json -Depth 12 -Compress