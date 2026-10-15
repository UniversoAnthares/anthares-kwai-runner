Set-StrictMode -Version Latest
$script:MemuRoot='D:\Program Files\Microvirt\MEmu'
$script:Manager='D:\Program Files\Microvirt\MEmuHyperv\MEmuManage.exe'
$script:MemuExe=Join-Path $script:MemuRoot 'MEmu.exe'
$script:Adb=Join-Path $script:MemuRoot 'adb.exe'
$script:Vm='MEmu_4'
$script:VmConfig='D:\Program Files\Microvirt\MEmu\MemuHyperv VMs\MEmu_4\MEmu_4.memu'
function Get-MEmuInfo {
    $r=Invoke-AntharesProcess $script:Manager @('showvminfo',$script:Vm,'--machinereadable') 7000
    $s=[string]$r.stdout
    $state=if($s -match '(?m)^VMState="([^"]+)"'){$matches[1]}else{'unknown'}
    $serial=if($s -match 'Forwarding\(\d+\)="ADB,tcp,127\.0\.0\.1,(\d+),'){"127.0.0.1:$($matches[1])"}else{$null}
    if(($state -eq 'unknown' -or -not $serial) -and (Test-Path $script:VmConfig)){
        $cfg=Get-Content $script:VmConfig -Raw
        if(-not $serial -and $cfg -match 'Forwarding name="ADB"[^>]*hostport="(\d+)"'){$serial="127.0.0.1:$($matches[1])"}
        if($state -eq 'unknown'){$state=if(Get-Process MEmuHeadless -ErrorAction SilentlyContinue){'running'}else{'poweroff'}}
    }
    [ordered]@{backend='memu4';vm=$script:Vm;vm_state=$state;serial=$serial;manager_ok=$r.ok;manager_error=[string]$r.stderr;config=$script:VmConfig}
}
function Start-MEmuManaged {
    $r=Invoke-AntharesProcess $script:Manager @('startvm',$script:Vm,'--type','headless') 30000
    if($r.ok){return [ordered]@{ok=$true;method='manager';detail=$r}}
    try {Start-ScheduledTask -TaskName 'Anthares-MEmu-Standby-Watchdog' -ErrorAction Stop; return [ordered]@{ok=$true;method='watchdog';detail=$r}} catch {return [ordered]@{ok=$false;method='watchdog';detail=$r;error=$_.Exception.Message}}
}
