# Run once in the Windows user account that will run the background bridge.
# All installed/runtime files are kept under D:\AntharesWork.
param([string]$Repository = 'UniversoAnthares/anthares-ara-queue',
      [string]$DeviceId = 'DESKTOP-FTDK0HP',
      [string]$WorkRoot = 'D:\AntharesWork\AntharesRemote',
      [string]$BridgePath = (Join-Path $PSScriptRoot 'github-queue-bridge.ps1'),
      [switch]$UseGhAuthToken)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $BridgePath)) { throw 'Bridge script missing' }
New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null
$secretDir = Join-Path $WorkRoot 'secrets'
New-Item -ItemType Directory -Path $secretDir -Force | Out-Null
if ($UseGhAuthToken) {
  $plain = (& gh auth token 2>$null | Select-Object -First 1).Trim()
  if ([string]::IsNullOrWhiteSpace($plain)) { throw 'gh is not authenticated' }
  $token = ConvertTo-SecureString $plain -AsPlainText -Force
} else {
  $token = Read-Host 'GitHub token for anthares-ara-queue (Issues read/write; Metadata read)' -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($token)
  try { $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
try {
  $headers = @{Authorization="Bearer $plain";Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28'}
  $info = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repository" -Headers $headers -TimeoutSec 15
  if (-not $info.private) { throw 'Repository must be private' }
} finally {
  Remove-Variable plain -ErrorAction SilentlyContinue
}
$token | ConvertFrom-SecureString | Set-Content -Path (Join-Path $secretDir 'github-queue-token.dpapi') -Encoding ASCII
$target = Join-Path $WorkRoot 'github-queue-bridge.ps1'
$src = (Resolve-Path $BridgePath).Path
$dst = [IO.Path]::GetFullPath($target)
if (-not [string]::Equals($src,$dst,[StringComparison]::OrdinalIgnoreCase)) { Copy-Item -Path $src -Destination $dst -Force }
$arg = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy RemoteSigned -File "' + $target + '" -Repository "' + $Repository + '" -DeviceId "' + $DeviceId + '" -WorkRoot "' + $WorkRoot + '"'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'Anthares-GitHub-Queue-Bridge' -Action $action -Trigger $trigger -Settings $settings -Description 'Background private GitHub queue bridge (ping-only validation)' -Force | Out-Null
Write-Host 'Configured under D:\AntharesWork. Existing ARA service was not modified.'
