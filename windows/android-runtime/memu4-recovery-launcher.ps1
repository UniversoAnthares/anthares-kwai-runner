$ErrorActionPreference='Continue'
$memuc='D:\Program Files\Microvirt\MEmu\memuc.exe'
$log='D:\AntharsWork\logs\memu4-recovery-launcher.log'
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Add-Content -LiteralPath $log -Encoding UTF8}catch{}}
Log 'fallback-launcher begin'
# Fallback owns the VM only after SYSTEM primary exhaustion. Replace an unusable
# Session 0 headless instance so memuc relaunches MEmu_4 in Lucas' interactive session.
$mySession=(Get-Process -Id $PID).SessionId
$foreign=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -eq 'MEmuHeadless.exe' -and $_.CommandLine -match '--comment\s+MEmu_4(?:\s|$)' -and $_.SessionId -ne $mySession})
foreach($h in $foreign){
  try{Log ("stopping unusable primary headless pid="+$h.ProcessId+" session="+$h.SessionId); Stop-Process -Id $h.ProcessId -Force -ErrorAction Stop}catch{Log ("failed stopping foreign headless: "+$_.Exception.Message)}
}
if($foreign.Count){Start-Sleep -Seconds 3}
try{
  $p=Start-Process -FilePath $memuc -ArgumentList @('start','-n','MEmu_4','-b') -Wait -PassThru -ErrorAction Stop
  Log ("memuc exit="+$p.ExitCode)
}catch{
  Log ("memuc failed: "+$_.Exception.Message)
  exit 2
}
$deadline=(Get-Date).AddSeconds(120)
$stable=0
while((Get-Date)-lt $deadline){
  $heads=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -eq 'MEmuHeadless.exe' -and $_.CommandLine -match '--comment\s+MEmu_4(?:\s|$)'})
  if($heads.Count -gt 0){
    $stable++
    if($stable -ge 3){
      Log ("headless stable pid="+(($heads.ProcessId)-join ',')+"; fallback launcher exits and returns authority to SYSTEM runtime")
      exit 0
    }
  }else{$stable=0}
  Start-Sleep -Seconds 2
}
Log 'headless not stable within 120s'
exit 3
