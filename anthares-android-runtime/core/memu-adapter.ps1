Set-StrictMode -Version Latest
$script:MemuRoot='D:\Program Files\Microvirt\MEmu'
$script:Manager='D:\Program Files\Microvirt\MEmuHyperv\MEmuManage.exe'
$script:Memuc=Join-Path $script:MemuRoot 'memuc.exe'
$script:MemuExe=Join-Path $script:MemuRoot 'MEmu.exe'
$script:Adb=Join-Path $script:MemuRoot 'adb.exe'
$script:Vm='MEmu_4'
$script:VmIndex='4'
$script:VmUuid='20261015-aaaa-aaaa-aaaa-000000000004'
$script:VmConfig='D:\Program Files\Microvirt\MEmu\MemuHyperv VMs\MEmu_4\MEmu_4.memu'
$script:MemuAdbServerPort=if($env:ANTHARES_MEMU_ADB_SERVER_PORT){[int]$env:ANTHARES_MEMU_ADB_SERVER_PORT}else{5037}
function Get-MEmuNativeProcess {
    try {
        Get-CimInstance Win32_Process -Filter "Name='MEmuHeadless.exe'" -ErrorAction Stop |
            Where-Object {$_.CommandLine -match [regex]::Escape($script:Vm) -or $_.CommandLine -match [regex]::Escape($script:VmUuid)} |
            Select-Object -First 1
    } catch {$null}
}
function Get-MEmuInfo {
    $r=Invoke-AntharesProcess $script:Manager @('showvminfo',$script:Vm,'--machinereadable') 7000
    $s=[string]$r.stdout
    $state=if($s -match '(?m)^VMState="([^"]+)"'){$matches[1]}else{'unknown'}
    $serial=if($s -match 'Forwarding\(\d+\)="ADB,tcp,127\.0\.0\.1,(\d+),'){"127.0.0.1:$($matches[1])"}else{$null}
    if(( -not $serial) -and (Test-Path $script:VmConfig)){
        $cfg=Get-Content $script:VmConfig -Raw
        if($cfg -match 'Forwarding name="ADB"[^>]*hostport="(\d+)"'){$serial="127.0.0.1:$($matches[1])"}
    }
    if(-not $serial){$serial='127.0.0.1:21543'}
    $native=Get-MEmuNativeProcess
    if($native){$state='running'}elseif($state -eq 'unknown'){$state='poweroff'}
    [ordered]@{backend='memu4';vm=$script:Vm;vm_state=$state;serial=$serial;adb_server_port=$script:MemuAdbServerPort;native_pid=if($native){[int]$native.ProcessId}else{$null};manager_ok=$r.ok;manager_error=[string]$r.stderr;config=$script:VmConfig}
}
function Start-MEmuManaged {
    $native=Get-MEmuNativeProcess
    if($native){return [ordered]@{ok=$true;method='already_running_native';pid=[int]$native.ProcessId}}
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    if($identity -notmatch '(?i)SYSTEM$'){
        $oldCompat=$env:__COMPAT_LAYER
        try {
            $env:__COMPAT_LAYER='RunAsInvoker'
            $r=Invoke-AntharesProcess $script:Memuc @('start','-i',$script:VmIndex) 30000
        } finally {$env:__COMPAT_LAYER=$oldCompat}
        if($r.ok){return [ordered]@{ok=$true;method='memuc_official_launcher';detail=$r}}
    }
    $user=if($env:ANTHARES_MEMU_INTERACTIVE_USER){$env:ANTHARES_MEMU_INTERACTIVE_USER}else{try{(Get-CimInstance Win32_ComputerSystem -ErrorAction Stop).UserName}catch{$null}}
    if([string]::IsNullOrWhiteSpace($user)){return [ordered]@{ok=$false;method='interactive_task';error='no_interactive_user'}}
    $task='Anthares-MEmu4-Interactive-Launcher'
    try {
        $action=New-ScheduledTaskAction -Execute $script:MemuExe -Argument $script:Vm -WorkingDirectory $script:MemuRoot
        $principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest
        $trigger=New-ScheduledTaskTrigger -AtLogOn -User $user
        $settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        Register-ScheduledTask -TaskName $task -Action $action -Principal $principal -Trigger $trigger -Settings $settings -Force | Out-Null
        Start-ScheduledTask -TaskName $task -ErrorAction Stop
        $deadline=(Get-Date).AddSeconds(30)
        do {Start-Sleep -Milliseconds 750;$native=Get-MEmuNativeProcess;if($native){return [ordered]@{ok=$true;method='interactive_native_launcher';user=$user;task=$task;pid=[int]$native.ProcessId}}} while((Get-Date)-lt $deadline)
        return [ordered]@{ok=$false;method='interactive_native_launcher';user=$user;task=$task;error='native_process_not_observed'}
    } catch {return [ordered]@{ok=$false;method='interactive_native_launcher';user=$user;task=$task;error=$_.Exception.Message}}
}

