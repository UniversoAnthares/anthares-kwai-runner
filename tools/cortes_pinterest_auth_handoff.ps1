# One-time interactive account authorization handoff.
# Never reads credentials or copies Chrome cookies. Only checks exact account.
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$ui=Join-Path $root 'tools\cortes_pinterest_browser_ui.mjs'
$closer=Join-Path $root 'tools\cortes_pinterest_close_browser.mjs'
$log='D:\AntharsWork\cortes-pinterest-auth-handoff.log'
$publisher='CORTES-Pinterest-Local'
$interactive='Anthares CORTES Pinterest Auth Interactive'
$headless='Anthares CORTES Pinterest Headless Browser Silent'
$watcher='Anthares CORTES Pinterest Auth Watchdog'
function Audit([string]$label){Add-Content -Path $log -Value ((Get-Date).ToUniversalTime().ToString('o')+' '+$label) -Encoding UTF8}
function Authenticated {
  try {
    $data=& node $ui --preflight 2>$null
    if($LASTEXITCODE -ne 0){return $false}
    foreach($line in @($data)){
      try {
        $p=$line|ConvertFrom-Json
        if($p.status -eq 'READY' -and $p.account_id -eq 'lucasyahn'){return $true}
      }catch{}
    }
  }catch{}
  return $false
}
try {
 if(-not (Authenticated)){exit 0}
 Audit 'AUTHENTICATED_PROFILE_VERIFIED'
 try{& node $closer 2>$null | Out-Null}catch{}
 Start-Sleep -Seconds 3
 try{Stop-ScheduledTask -TaskName $interactive -ErrorAction SilentlyContinue}catch{}
 Start-ScheduledTask -TaskName $headless
 Start-Sleep -Seconds 5
 if(Authenticated){
    Enable-ScheduledTask -TaskName $publisher|Out-Null
    Audit 'HEADLESS_SESSION_VERIFIED_PUBLISHER_ENABLED'
    Start-ScheduledTask -TaskName $publisher
    Disable-ScheduledTask -TaskName $watcher|Out-Null
    exit 0
 }
 Audit 'HEADLESS_SESSION_NOT_VERIFIED_RETURN_TO_INTERACTIVE'
 try{Stop-ScheduledTask -TaskName $headless -ErrorAction SilentlyContinue}catch{}
 Start-Sleep -Seconds 2
 Start-ScheduledTask -TaskName $interactive
 exit 3
}catch{
 Audit 'HANDOFF_ERROR_NO_PUBLISH'
 exit 4
}
