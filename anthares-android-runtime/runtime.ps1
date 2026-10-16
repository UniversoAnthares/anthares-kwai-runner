param(
 [ValidateSet('status','health','devices','recover','packages','foreground','launch','identity-probe')][string]$Action='status',
 [string]$Package=''
)
$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesAndroidRuntime'
. "$root\core\transport-adb.ps1"
. "$root\core\memu-adapter.ps1"
function Get-RuntimeHealth {
    $i=Get-MEmuInfo
    $port=[int]$i.adb_server_port
    $d=Get-AdbDevices -Adb $script:Adb -ServerPort $port
    $transport=if($i.serial -and $d.devices.Contains($i.serial)){$d.devices[$i.serial]}else{'missing'}
    $ready=$false;$boot=$null
    if($transport -eq 'device'){
      $boot=Invoke-AntharesAdb -Adb $script:Adb -Args @('-s',$i.serial,'shell','getprop','sys.boot_completed') -TimeoutMs 5000 -ServerPort $port
      $ready=([string]$boot.stdout).Trim() -eq '1'
    }
    $score=0;if($i.vm_state -eq 'running'){$score+=25};if($transport -eq 'device'){$score+=35};if($ready){$score+=40}
    $state=if($ready){'ANDROID_READY'}elseif($i.vm_state -eq 'running' -and $transport -ne 'device'){'RUNNING_TRANSPORT_OFFLINE'}elseif($i.vm_state -in @('poweroff','aborted','saved')){'STOPPED'}else{'DEGRADED'}
    [ordered]@{ok=$ready;backend='memu4';vm_state=$i.vm_state;serial=$i.serial;adb_server_port=$port;native_pid=$i.native_pid;transport_state=$transport;android_ready=$ready;health_score=$score;state=$state;manager_ok=$i.manager_ok;manager_error=$i.manager_error}
}
function Save-Event($operation,$result){
    if(!(Test-Path $root)){New-Item -ItemType Directory -Force $root|Out-Null}
    $e=[ordered]@{time=(Get-Date).ToUniversalTime().ToString('o');operation=$operation;result=$result}
    ($e|ConvertTo-Json -Depth 8 -Compress)|Add-Content "$root\events.jsonl"
    $e|ConvertTo-Json -Depth 8|Set-Content "$root\state.json"
}
function Recover-Runtime {
    $h=Get-RuntimeHealth
    if($h.android_ready){return [ordered]@{ok=$true;action='already_ready';health=$h}}
    if($h.vm_state -in @('poweroff','aborted','saved')){
        $s=Start-MEmuManaged
        if(-not $s.ok){$o=[ordered]@{ok=$false;reason='backend_start_failed';start=$s;health=$h};Save-Event recover $o;return $o}
        Start-Sleep -Seconds 4
        $h=Get-RuntimeHealth
    }
    if(-not $h.serial){$o=[ordered]@{ok=$false;reason='serial_missing';health=$h};Save-Event recover $o;return $o}
    $port=[int]$h.adb_server_port
    # The canonical SYSTEM runtime uses ADB port 5037. Port 5038 is reserved for the interactive recovery fallback only.
    # Never kill/restart it from SYSTEM: doing so changes ADB key context and can turn a healthy guest into offline.
    $steps=@(@('disconnect',$h.serial),@('connect',$h.serial),@('connect',$h.serial))
    foreach($s in $steps){
      [void](Invoke-AntharesAdb -Adb $script:Adb -Args $s -TimeoutMs 5000 -ServerPort $port)
      1..6|ForEach-Object{Start-Sleep -Seconds 1;$x=Get-RuntimeHealth;if($x.android_ready){$o=[ordered]@{ok=$true;action='adb_recovered';health=$x};Save-Event recover $o;return $o}}
    }
    $o=[ordered]@{ok=$false;reason='transport_recovery_exhausted';health=(Get-RuntimeHealth)};Save-Event recover $o;return $o
}
$h=Get-RuntimeHealth
$port=[int]$h.adb_server_port
switch($Action){
 'status' {$out=$h}
 'health' {$out=$h}
 'devices' {$out=Get-AdbDevices -Adb $script:Adb -ServerPort $port}
 'recover' {$out=Recover-Runtime}
 'packages' {if($h.transport_state -eq 'device'){$out=Invoke-AntharesAdb -Adb $script:Adb -Args @('-s',$h.serial,'shell','pm','list','packages') -TimeoutMs 8000 -ServerPort $port}else{$out=[ordered]@{ok=$false;reason='transport_unavailable';health=$h}}}
 'foreground' {if($h.transport_state -eq 'device'){$out=Invoke-AntharesAdb -Adb $script:Adb -Args @('-s',$h.serial,'shell','dumpsys','window','windows') -TimeoutMs 8000 -ServerPort $port}else{$out=[ordered]@{ok=$false;reason='transport_unavailable';health=$h}}}
 'launch' {if($h.transport_state -eq 'device' -and $Package){$out=Invoke-AntharesAdb -Adb $script:Adb -Args @('-s',$h.serial,'shell','monkey','-p',$Package,'1') -TimeoutMs 10000 -ServerPort $port}else{$out=[ordered]@{ok=$false;reason='transport_or_package_unavailable';health=$h}}}
 'identity-probe' {if($h.transport_state -eq 'device'){$out=[ordered]@{ok=$true;uiautomator=(Invoke-AntharesAdb -Adb $script:Adb -Args @('-s',$h.serial,'shell','uiautomator','dump','/sdcard/anthares-ui.xml') -TimeoutMs 10000 -ServerPort $port);pull=(Invoke-AntharesAdb -Adb $script:Adb -Args @('-s',$h.serial,'pull','/sdcard/anthares-ui.xml',"$root\anthares-ui.xml") -TimeoutMs 10000 -ServerPort $port)}}else{$out=[ordered]@{ok=$false;reason='transport_unavailable';health=$h}}}
}
$out|ConvertTo-Json -Depth 10 -Compress

