$ErrorActionPreference='Stop'
$stageRoot='D:\AntharsWork\AntharesRemoteAgent'
$installRoot='C:\ProgramData\AntharesRemoteAgent'
$workRoot='D:\AntharsWork'
$result=Join-Path $workRoot 'legacy-pc-runtime\supervisor\phase4-migration-result.json'
$newExe=Join-Path $stageRoot 'anthares-remote-agent-v4.phase4.new.exe'
$exe=Join-Path $installRoot 'anthares-remote-agent-v4.exe'
$backup=Join-Path $installRoot 'anthares-remote-agent-v4.pre-phase4.exe'
$installer=Join-Path $PSScriptRoot 'install-system-v8.ps1'
New-Item -ItemType Directory -Force -Path $installRoot,(Split-Path $result) | Out-Null
try{
  $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
  $principal=[Security.Principal.WindowsPrincipal]::new($identity)
  if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Phase 4 migration must run elevated/SYSTEM'}
  if(-not(Test-Path $newExe)){throw 'staged V4 missing'}
  if(-not(Test-Path $installer)){throw 'canonical install-system-v8.ps1 missing beside migration script'}
  $newHash=(Get-FileHash $newExe -Algorithm SHA256).Hash
  $oldHash=''
  if(Test-Path $exe){$oldHash=(Get-FileHash $exe -Algorithm SHA256).Hash;Copy-Item $exe $backup -Force}
  Copy-Item $newExe $exe -Force
  if((Get-FileHash $exe -Algorithm SHA256).Hash -ne $newHash){throw 'staged V4 copy verification failed'}
  & $installer
  $installResult=Join-Path $workRoot 'legacy-pc-runtime\supervisor\install-result.json'
  if(-not(Test-Path $installResult)){throw 'canonical installer did not produce install-result.json'}
  $verified=Get-Content $installResult -Raw | ConvertFrom-Json
  if(-not $verified.ok -or -not $verified.queue_credential_validated -or -not $verified.queue_end_to_end_proof -or -not $verified.mcp_http_transport_configured -or [int]$verified.system_v4_pid -le 0){throw 'canonical SYSTEM installation did not prove dual-transport runtime'}
  [pscustomobject]@{ok=$true;old_hash=$oldHash;new_hash=$newHash;installed_hash=(Get-FileHash $exe -Algorithm SHA256).Hash;install_root=$installRoot;work_root=$workRoot;system_v4_pid=$verified.system_v4_pid;queue_end_to_end_proof=$true;mcp_http_transport_configured=$true;queue_proof_issue=$verified.queue_proof_issue;at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content $result -Encoding UTF8
}catch{
  if((Test-Path $backup) -and (Test-Path $exe)){try{Copy-Item $backup $exe -Force}catch{}}
  [pscustomobject]@{ok=$false;error=$_.Exception.Message;install_root=$installRoot;work_root=$workRoot;at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json|Set-Content $result -Encoding UTF8
  throw
}
