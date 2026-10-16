$ErrorActionPreference='Continue'
$memuc='D:\Program Files\Microvirt\MEmu\memuc.exe'
$log='D:\AntharsWork\logs\memu4-recovery-launcher.log'
function Log([string]$m){try{"$(Get-Date -Format o) $m"|Add-Content -LiteralPath $log -Encoding UTF8}catch{}}
Log 'launcher-v2 begin'
try{
  $p=Start-Process -FilePath $memuc -ArgumentList @('start','-n','MEmu_4','-b') -Wait -PassThru -ErrorAction Stop
  Log ("memuc exit="+$p.ExitCode)
}catch{
  Log ("memuc failed: "+$_.Exception.Message)
  exit 2
}
$deadline=(Get-Date).AddSeconds(120)
$seen=$false
while($true){
  $heads=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -eq 'MEmuHeadless.exe' -and $_.CommandLine -match '--comment\s+MEmu_4(?:\s|$)'})
  if($heads.Count -gt 0){
    if(-not $seen){Log ("headless seen pid="+(($heads.ProcessId)-join ','));$seen=$true}
  } elseif($seen){
    Log 'headless disappeared; launcher exiting'
    break
  } elseif((Get-Date)-gt $deadline){
    Log 'headless not seen within 120s'
    exit 3
  }
  Start-Sleep -Seconds 5
}
exit 0
