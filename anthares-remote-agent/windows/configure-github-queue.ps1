# Run once in the Windows user account that will run the background bridge.
# Does not touch the existing ARA service or Cloudflare/Render endpoints.
param([string]$Repository = 'UniversoAnthares/anthares-ara-queue',
      [string]$DeviceId = 'DESKTOP-FTDK0HP',
      [string]$BridgePath = (Join-Path $PSScriptRoot 'github-queue-bridge.ps1'))
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $BridgePath)) { throw 'Bridge script missing' }
$token = Read-Host 'GitHub fine-grained token (Issues: read/write; Metadata: read)' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
try {
  $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
  $headers = @{Authorization="Bearer $plain";Accept='application/vnd.github+json'}
  $info = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repository" -Headers $headers -TimeoutSec 15
  if (-not $info.private) { throw 'Repository must be private' }
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
  Remove-Variable plain -ErrorAction SilentlyContinue
}
$dir = Join-Path $env:APPDATA 'AntharesRemoteAgent'
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$token | ConvertFrom-SecureString | Set-Content -Path (Join-Path $dir 'github-queue-token.dpapi') -Encoding ASCII
$target = Join-Path $dir 'github-queue-bridge.ps1'
Copy-Item -Path $BridgePath -Destination $target -Force
$arg = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy RemoteSigned -File "' + $target + '" -Repository "' + $Repository + '" -DeviceId "' + $DeviceId + '"'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'Anthares-GitHub-Queue-Bridge' -Action $action -Trigger $trigger -Settings $settings -Description 'Background GitHub queue connectivity bridge (ping only)' -Force | Out-Null
Write-Host 'Configured private GitHub queue with user-scoped DPAPI credential and hidden at-logon task.'
Write-Host 'Task is not started automatically during configuration. Existing ARA remains untouched.'
