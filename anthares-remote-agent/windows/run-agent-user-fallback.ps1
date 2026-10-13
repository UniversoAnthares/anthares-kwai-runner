$ErrorActionPreference='SilentlyContinue'
# Deprecated by Phase 4. Canonical execution is SYSTEM-only.
try{Disable-ScheduledTask -TaskName 'Anthares Remote Agent User' -ErrorAction SilentlyContinue|Out-Null}catch{}
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{
  $_.SessionId -ne 0 -and $_.Name -match '^anthares-remote-agent(?:-v4|-standard)?\.exe$'
}|ForEach-Object{try{Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue}catch{}}
exit 0
