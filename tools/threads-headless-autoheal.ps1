$ErrorActionPreference='Stop'
$root='D:\AntharsWork\cortes-social-browser-20261020'
$pub='Anthares CORTES Threads Browser Publisher'
$lock=Join-Path $root 'threads-worker.lock'
$log=Join-Path $root 'threads-headless-autoheal.log'
function Log([string]$message) {
 [IO.File]::AppendAllText($log,([DateTime]::UtcNow.ToString('o')+' '+$message+[Environment]::NewLine))
}
if(Test-Path $lock){Log 'SKIPPED_LOCK_ACTIVE';exit 4}
if((Get-ScheduledTask -TaskName $pub).State -eq 'Running'){Log 'SKIPPED_PUBLISHER_RUNNING';exit 4}
$roots=@(Get-CimInstance Win32_Process | Where-Object {
 $_.Name -eq 'chrome.exe' -and $_.CommandLine -match '--headless' -and
 $_.CommandLine -match '--remote-debugging-port=9225' -and
 $_.CommandLine -match 'browser-profiles\\AntharesMeta' -and
 $_.CommandLine -notmatch '--type='
})
if($roots.Count -gt 1){Log 'BLOCKED_MULTIPLE_ROOTS';exit 5}
foreach($p in $roots){Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop}
Start-Sleep -Seconds 3
if(Test-Path $lock){Log 'BLOCKED_LOCK_CHANGED';exit 4}
$pythonw='C:\Users\Lucas\AppData\Local\Programs\Python\Python311\pythonw.exe'
$launcher=Join-Path $root 'threads-headless-recover.py'
if(!(Test-Path $pythonw) -or !(Test-Path $launcher)){Log 'MISSING_LAUNCHER';exit 5}
& $pythonw $launcher
Start-Sleep -Seconds 6
try{$version=Invoke-RestMethod 'http://127.0.0.1:9225/json/version' -TimeoutSec 5
if(!$version.Browser){throw 'CDP_NO_BROWSER'}
Log ('SUCCESS '+$version.Browser);exit 0}
catch{Log ('FAILED '+$_.Exception.GetType().Name);exit 6}
