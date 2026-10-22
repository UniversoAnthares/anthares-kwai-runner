# Anthares X autonomous five-minute hidden recovery. Dedicated Chrome only.
$ErrorActionPreference='Stop'
$root='D:\AntharsWork\x-reliability-qa-20261021'
$dir='D:\AntharsWork\x-watchdog'
New-Item -ItemType Directory -Force $dir|Out-Null
$now=Get-Date
$report=[ordered]@{time=$now.ToString('o');cdp=$false;publisher='unknown';source='unknown';recoveries=@();incidents=@()}
function CdpReady {
 try {
  $r=Invoke-RestMethod 'http://127.0.0.1:9224/json/version' -TimeoutSec 4
  return [bool]($r.'Browser' -and $r.'webSocketDebuggerUrl')
 } catch {return $false}
}
function LaunchTask($name,$reason) {
 try {
  $t=Get-ScheduledTask -TaskName $name -ErrorAction Stop
  if($t.State -eq 'Disabled'){Enable-ScheduledTask -TaskName $name -ErrorAction Stop|Out-Null}
  if($t.State -ne 'Running'){Start-ScheduledTask -TaskName $name -ErrorAction Stop;$script:report.recoveries+= $reason}
 }catch{$script:report.incidents+= ($reason+'_FAILED')}
}
function AlertQa($incident) {
 $stamp=$now.ToString('yyyyMMdd')
 $guard=Join-Path $dir ('p0-'+$stamp+'-'+$incident+'.flag')
 if(Test-Path $guard){return}
 New-Item -ItemType File -Path $guard -Force|Out-Null
 try{ & gh api 'repos/UniversoAnthares/anthares-kwai-runner/issues/380/comments' -X POST -f ('body=X_WATCHDOG_P0 '+$stamp+' '+$incident) 1>$null 2>$null }catch{}
}
try {
 $report.cdp=CdpReady
 if(-not $report.cdp) {
  $chrome=Get-CimInstance Win32_Process -Filter "name='chrome.exe'" |
    Where-Object{$_.CommandLine -like '*AntharesXBridge*' -and $_.CommandLine -notlike '*--type=*'}
  if(@($chrome).Count -eq 0) {
   LaunchTask 'Anthares X Browser Persistent' 'CHROME_TASK'
   Start-Sleep -Seconds 7
   $report.cdp=CdpReady
   if(-not $report.cdp) {
    $exe='C:\Program Files\Google\Chrome\Application\chrome.exe'
    if(Test-Path $exe) {
     $args='--remote-debugging-port=9224 --remote-debugging-address=127.0.0.1 --user-data-dir="D:\AntharsWork\browser-profiles\AntharesXBridge" --profile-directory=Default --no-first-run --no-default-browser-check --disable-sync --mute-audio --disable-notifications --window-position=-32000,-32000 --window-size=1366,768 https://x.com/home'
     try {
      Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden|Out-Null
      Start-Sleep -Seconds 7
      $report.cdp=CdpReady
      if($report.cdp){$report.recoveries+='CHROME_INDEPENDENT'}
     }catch{$report.incidents+='CHROME_INDEPENDENT_FAILED'}
    }
   }
  }else{$report.incidents+='DEDICATED_CHROME_RUNNING_NO_CDP'}
 }
 if(-not $report.cdp){$report.incidents+='X_BROWSER_UNAVAILABLE'}
 $pub='Anthares X Durable Local Standby'
 $src='Anthares X Longform Source Fallback'
 foreach($name in @($pub,$src)) {
  $t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if(-not $t){
   $installer=if($name -eq $pub){Join-Path $root 'x_install_windows_fallback.ps1'}else{Join-Path $root 'x_install_windows_source_fallback.ps1'}
   if(Test-Path $installer){
    try{& $installer 1>$null 2>$null;$report.recoveries+=($name+'_REINSTALLED')}
    catch{$report.incidents+=($name+'_REINSTALL_FAILED')}
   }else{$report.incidents+=($name+'_MISSING')}
  }
 }
 $t=Get-ScheduledTask -TaskName $pub -ErrorAction SilentlyContinue
 if($t) {
  $report.publisher=[string]$t.State
  if($report.cdp -and $t.State -ne 'Running') {
   $info=Get-ScheduledTaskInfo -TaskName $pub
   if($t.State -eq 'Disabled' -or $info.LastRunTime -lt $now.AddMinutes(-19)) {
    LaunchTask $pub 'PUBLISHER_STALE_RESTART'
   }
  }
 }
 $s=Get-ScheduledTask -TaskName $src -ErrorAction SilentlyContinue
 if($s) {
  $report.source=[string]$s.State
  if($s.State -ne 'Running') {
   $info=Get-ScheduledTaskInfo -TaskName $src
   if($s.State -eq 'Disabled' -or $info.LastRunTime -lt $now.AddMinutes(-145)) {
    LaunchTask $src 'SOURCE_STALE_RESTART'
   }
  }
 }
}catch{$report.incidents+=('WATCHDOG_EXCEPTION_'+$_.Exception.GetType().Name)}
$tmp=Join-Path $dir 'x-watchdog-state.tmp'
$dest=Join-Path $dir 'x-watchdog-state.json'
[IO.File]::WriteAllText($tmp,($report|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
Move-Item -Force $tmp $dest
foreach($problem in $report.incidents){AlertQa $problem}

# Independent cloud QA path. The script is cached locally and refreshed
# every watchdog tick; lack of GitHub access never prevents local recovery.
$qaSource=Join-Path $root 'tools\x_cloud_qa_watchdog.py'
try {
  New-Item -ItemType Directory -Path (Split-Path $qaSource) -Force|Out-Null
  $base64=& gh api 'repos/UniversoAnthares/anthares-kwai-runner/contents/tools/x_cloud_qa_watchdog.py?ref=main' --jq '.content'
  if($LASTEXITCODE -ne 0){throw 'X_CLOUD_QA_SYNC_UNAVAILABLE'}
  $binary=[Convert]::FromBase64String(($base64 -join '' -replace '\s',''))
  [IO.File]::WriteAllBytes(($qaSource+'.new'),$binary)
  & 'C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe' -m py_compile ($qaSource+'.new') 1>$null 2>$null
  if($LASTEXITCODE -ne 0){throw 'X_CLOUD_QA_SOURCE_INVALID'}
  Move-Item -Force ($qaSource+'.new') $qaSource
}catch{}
if(Test-Path $qaSource){
 try {
  & 'C:\Users\Lucas\AppData\Local\Programs\Python\Python311\python.exe' $qaSource 1>$null 2>$null
 }catch {
  AlertQa 'X_CLOUD_QA_LOCAL_EXEC_FAILED'
 }
}

