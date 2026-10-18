param([switch]$Visible)
$ErrorActionPreference='Stop'
# Administrative session only. This does not select or alter a publishing backend.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management\Microsoft.PowerShell.Management.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules\CimCmdlets\CimCmdlets.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules\NetTCPIP\NetTCPIP.psd1') -ErrorAction Stop
$profileRoot='D:\AntharsWork\browser-profiles\AntharesGitLab'
$chrome='C:\Program Files\Google\Chrome\Application\chrome.exe'
$endpoint='http://127.0.0.1:9223/json/version'
$created=$false
$mutex=New-Object Threading.Mutex($true,'Local\AntharesGitLabAdministrativeBrowserV1',[ref]$created)
if(-not $created){exit 0}
try{
    try{$version=Invoke-RestMethod -Uri $endpoint -TimeoutSec 3}catch{$version=$null}
    if($version.Browser){
        $listeners=@(Get-NetTCPConnection -LocalPort 9223 -State Listen -ErrorAction Stop)
        foreach($listener in $listeners){
            if($listener.LocalAddress -notin @('127.0.0.1','::1')){throw 'CDP must remain loopback-only'}
            $owner=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listener.OwningProcess)
            if($owner.Name -ne 'chrome.exe' -or $owner.CommandLine -notlike ('*'+$profileRoot+'*') -or $owner.CommandLine -notlike '*--remote-debugging-port=9223*'){throw 'CDP owner is not the dedicated administrative profile'}
        }
        [pscustomobject]@{ok=$true;state='already-ready';profile='AntharesGitLab';port=9223}|ConvertTo-Json -Compress;exit 0
    }
    if(-not (Test-Path -LiteralPath $chrome)){throw 'Dedicated Chromium executable missing'}
    if(-not (Test-Path -LiteralPath $profileRoot)){throw 'Existing dedicated profile missing; do not substitute a personal profile'}
    $arguments=@('--remote-debugging-port=9223','--remote-debugging-address=127.0.0.1',('--user-data-dir="'+$profileRoot+'"'),'--profile-directory=Default','--no-first-run','--no-default-browser-check','--disable-sync','--disable-extensions','--mute-audio','--disable-notifications')
    if(-not $Visible){$arguments+='--headless=new'}
    $arguments+='about:blank'
    $start=New-Object Diagnostics.ProcessStartInfo
    $start.FileName=$chrome;$start.Arguments=($arguments -join ' ');$start.UseShellExecute=$false;$start.CreateNoWindow=$true
    if(-not $Visible){$start.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden}
    [void][Diagnostics.Process]::Start($start)
    for($attempt=0;$attempt -lt 10;$attempt++){
        Start-Sleep -Milliseconds 500
        try{$version=Invoke-RestMethod -Uri $endpoint -TimeoutSec 2}catch{continue}
        if($version.Browser){[pscustomobject]@{ok=$true;state='recovered';profile='AntharesGitLab';port=9223;muted=$true;headless=(-not $Visible)}|ConvertTo-Json -Compress;exit 0}
    }
    throw 'Dedicated browser is not ready; preserve other Chrome sessions and fail closed'
}finally{
    try{$mutex.ReleaseMutex()}catch{};$mutex.Dispose()
}
