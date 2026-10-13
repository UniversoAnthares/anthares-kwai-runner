# Optional GitHub Issues control channel. Never enable without a PRIVATE repository.
# Completed/started IDs are never executed again automatically.
param([string]$Repository = $env:ANTHARES_GITHUB_QUEUE_REPOSITORY,
      [string]$Token = $env:ANTHARES_GITHUB_QUEUE_TOKEN,
      [string]$DeviceId = 'DESKTOP-FTDK0HP',
      [string]$WorkRoot = $(if ($env:ANTHARES_WORK_ROOT) { $env:ANTHARES_WORK_ROOT } else { 'D:\AntharesWork\AntharesRemote' }),
      [int]$IntervalSeconds = 30)
$ErrorActionPreference = 'Stop'
if ($Repository -notmatch '^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$') { throw 'Private repository owner/name required' }
$credentialFile = Join-Path $WorkRoot 'secrets\github-queue-token.dpapi'
if ([string]::IsNullOrWhiteSpace($Token) -and (Test-Path $credentialFile)) {
  $secure = Get-Content $credentialFile -Raw | ConvertTo-SecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { $Token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
if ([string]::IsNullOrWhiteSpace($Token)) { throw 'GitHub queue token required (environment or D:\AntharesWork DPAPI credential)' }
$sha256 = [Security.Cryptography.SHA256]::Create()
try { $repoHash = ([BitConverter]::ToString($sha256.ComputeHash([Text.Encoding]::UTF8.GetBytes($Repository.ToLowerInvariant()))) -replace '-', '').Substring(0,16) } finally { $sha256.Dispose() }
$root = Join-Path $WorkRoot ('github-queue\' + $repoHash)
New-Item -ItemType Directory -Path $root -Force | Out-Null
$headers = @{Authorization = "Bearer $Token"; Accept = 'application/vnd.github+json'; 'X-GitHub-Api-Version' = '2022-11-28'}
$api = "https://api.github.com/repos/$Repository"
$repoInfo = Invoke-RestMethod -Headers $headers -Uri $api -TimeoutSec 15
if (-not $repoInfo.private) { throw 'Refusing public queue: command payloads must remain private' }
$created = $false
$mutex = [System.Threading.Mutex]::new($true, 'Global\AntharesGithubQueueBridgeV1', [ref]$created)
if (-not $created) { exit 0 }
try {
  while ($true) {
    try {
      $issues = @(Invoke-RestMethod -Headers $headers -Uri "$api/issues?state=open&labels=ara-queued&per_page=30" -TimeoutSec 15)
      foreach ($issue in $issues) {
        if ($issue.pull_request) { continue }
        $number = [int]$issue.number
        $id = [string]$number
        $receipt = Join-Path $root ($id + '.started.json')
        if (Test-Path $receipt) {
          $prior = Get-Content $receipt -Raw | ConvertFrom-Json
          if ($prior.state -eq 'acknowledged') {
            try { Invoke-RestMethod -Method Delete -Headers $headers -Uri "$api/issues/$number/labels/ara-queued" -TimeoutSec 15 | Out-Null } catch {}
          }
          continue
        }
        $job = $null
        try { $job = $issue.body | ConvertFrom-Json -ErrorAction Stop } catch { continue }
        if ($job.device_id -ne $DeviceId -or $job.type -ne 'ping') { continue }
        $stream = $null
        try { $stream = [System.IO.File]::Open($receipt, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None) } catch { continue }
        try {
          $bytes = [Text.Encoding]::UTF8.GetBytes((@{id=$id;state='started'} | ConvertTo-Json -Compress))
          $stream.Write($bytes, 0, $bytes.Length)
          $stream.Flush($true)
        } finally { $stream.Dispose() }
        $body = @{body = "ARA result: ping=pong; device=$DeviceId; issue=$number"} | ConvertTo-Json
        Invoke-RestMethod -Method Post -Headers $headers -ContentType 'application/json' -Body $body -Uri "$api/issues/$number/comments" -TimeoutSec 15 | Out-Null
        @{id=$id;state='acknowledged'} | ConvertTo-Json -Compress | Set-Content -Path $receipt -Encoding UTF8
        Invoke-RestMethod -Method Delete -Headers $headers -Uri "$api/issues/$number/labels/ara-queued" -TimeoutSec 15 | Out-Null
      }
    } catch {
      Write-Error -Message ('GitHub queue poll deferred: ' + $_.Exception.Message) -ErrorAction Continue
    }
    Start-Sleep -Seconds ([Math]::Max(10, $IntervalSeconds))
  }
} finally {
  try { $mutex.ReleaseMutex() } catch {}
  $mutex.Dispose()
}
