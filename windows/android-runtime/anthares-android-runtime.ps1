param(
  [ValidateSet('health','select','recover','launch','foreground','ui','identity')][string]$Command='health',
  [ValidateSet('auto','physical','memu')][string]$Target='auto',
  [ValidateSet('IDLE','LEASED','STARTED','COMMITTING','UNCERTAIN','VERIFIED')][string]$PublicationState='IDLE',
  [switch]$AllowBackendStart,
  [switch]$AllowBackendReset
)
$ErrorActionPreference='Stop'
$Root='C:\ProgramData\AntharesAndroidRuntime'
$Adb='D:\Program Files\Microvirt\MEmu\adb.exe'
$AdbServerPort=5037
$Mgr='D:\Program Files\Microvirt\MEmuHyperv\MEmuManage.exe'
$Memuc='D:\Program Files\Microvirt\MEmu\memuc.exe'
$Vm='MEmu_4'
$VmIndex='4'
$PhysicalSerial=if($env:ANTHARES_PHYSICAL_ADB_SERIAL){$env:ANTHARES_PHYSICAL_ADB_SERIAL}else{'993fce720408'}

# MEmuHyperv keeps its canonical registry under Lucas' interactive profile.
# Anthares Remote runs as SYSTEM, so force the canonical profile before every
# hypervisor/memuc invocation instead of allowing a SYSTEM-local registry split.
$env:USERPROFILE='C:\Users\Lucas'
$env:HOMEDRIVE='C:'
$env:HOMEPATH='\Users\Lucas'
$env:ADB_VENDOR_KEYS='C:\Users\Lucas\.android\adbkey'

New-Item -ItemType Directory -Force -Path $Root | Out-Null

function Run([string]$File,[string[]]$Arguments,[int]$Timeout=12){
  $psi=New-Object Diagnostics.ProcessStartInfo
  $psi.FileName=$File;$psi.UseShellExecute=$false;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true
  $psi.Arguments=(($Arguments|ForEach-Object{if($_ -match '\s'){ '"'+$_+'"' }else{$_}})-join ' ')
  $p=New-Object Diagnostics.Process;$p.StartInfo=$psi
  try{[void]$p.Start();$o=$p.StandardOutput.ReadToEndAsync();$e=$p.StandardError.ReadToEndAsync();if(-not $p.WaitForExit($Timeout*1000)){try{$p.Kill()}catch{};return @{ok=$false;timeout=$true;stdout='';stderr='timeout'}};@{ok=($p.ExitCode -eq 0);code=$p.ExitCode;stdout=$o.Result;stderr=$e.Result}}catch{@{ok=$false;code=$null;stdout='';stderr=$_.Exception.Message}}finally{if($p){$p.Dispose()}}
}
function Event([string]$Op,$Data){
  $row=[ordered]@{timestamp=(Get-Date).ToUniversalTime().ToString('o');operation=$Op;data=$Data}
  ($row|ConvertTo-Json -Depth 12 -Compress)|Add-Content -Encoding UTF8 (Join-Path $Root 'events.jsonl')
  $row|ConvertTo-Json -Depth 12|Set-Content -Encoding UTF8 (Join-Path $Root 'state.json')
  $Data
}
function Adb([string[]]$Arguments,[string]$Serial=$null,[int]$Timeout=10){$a=@('-P',[string]$AdbServerPort);if($Serial){$a+=@('-s',$Serial)};$a+=$Arguments;Run -File $Adb -Arguments $a -Timeout $Timeout}
function Devices{
  $r=Adb @('devices','-l');$d=@{}
  foreach($line in (($r.stdout -split "`r?`n")|Select-Object -Skip 1)){$p=$line.Trim() -split '\s+';if($p.Count -ge 2){$d[$p[0]]=$p[1]}}
  $d
}
function MemuInfo{
  $r=Run -File $Mgr -Arguments @('showvminfo',$Vm,'--machinereadable') -Timeout 10;$txt=$r.stdout;$state='unknown';$serial=$null;$managerState='unknown';$reconciled=$false
  if($txt -match '(?m)^VMState="([^"]+)"'){$state=$Matches[1];$managerState=$state}
  if($txt -match 'Forwarding\(\d+\)="ADB,tcp,127\.0\.0\.1,(\d+),'){$serial='127.0.0.1:'+$Matches[1]}
  $live=Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -eq 'MEmuHeadless.exe' -and $_.CommandLine -match '--comment\s+MEmu_4(?:\s|$)'} | Select-Object -First 1
  if($live -and $state -ne 'running'){$state='running';$reconciled=$true}
  [ordered]@{state=$state;manager_state=$managerState;state_reconciled=$reconciled;serial=$serial;manager_ok=$r.ok;manager_error=$r.stderr.Trim()}
}
function MemuGuest([string]$Command,[int]$Timeout=8){Run -File $Memuc -Arguments @('-n',$Vm,'execcmd',$Command) -Timeout $Timeout}
function RemoveAbortedMemuOrphan{
  $m=MemuInfo
  if($m.state -ne 'aborted'){return [ordered]@{ok=$true;action='not_applicable';state=$m.state;terminated=@()}}
  $terminated=@()
  $ps=Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.Name -eq 'MEmuHeadless.exe' -and $_.CommandLine -match '--comment\s+MEmu_4(?:\s|$)'}
  foreach($p in $ps){
    try{Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop;$terminated+=[int]$p.ProcessId}catch{}
  }
  Start-Sleep -Milliseconds 800
  [ordered]@{ok=$true;action=if($terminated.Count){'terminated_aborted_orphan'}else{'none_found'};state=$m.state;terminated=$terminated}
}
function StartMemuOfficial{
  $m=MemuInfo
  if($m.state -eq 'running'){return @{ok=$true;action='already_running';authority='system';stdout='';stderr=''}}
  $cleanup=if($m.state -eq 'aborted'){RemoveAbortedMemuOrphan}else{$null}

  # PRIMARY AUTHORITY: SYSTEM starts MEmu directly, headless.
  $direct=Run -File $Mgr -Arguments @('startvm',$Vm,'--type','headless') -Timeout 35
  $directDeadline=(Get-Date).AddSeconds(75)
  do{
    [void](Adb @('start-server') $null 8)
    $mi=MemuInfo
    if($mi.serial){[void](Adb @('connect',$mi.serial) $null 8)}
    $after=Probe 'memu'
    if($after.healthy){return @{ok=$true;action='system_headless_primary_healthy';authority='system';stdout=$direct.stdout;stderr=$direct.stderr;cleanup=$cleanup;after=$after}}
    if($mi.state -eq 'running'){
      $guestRepair=RepairGuestAdbTcp
      if($guestRepair.ok){return @{ok=$true;action='system_headless_primary_recovered';authority='system';stdout=$direct.stdout;stderr=$direct.stderr;cleanup=$cleanup;after=$guestRepair.after;guest_repair=$guestRepair}}
    }
    Start-Sleep -Seconds 3
  }while((Get-Date)-lt $directDeadline)

  # REDUNDANCY ONLY: interactive path is allowed only after SYSTEM path failed.
  $launcherTask='Anthares-MEmu4-Recovery-Launcher'
  $adbTask='Anthares-MEmu4-ADB5038-Interactive'
  $fallback=[ordered]@{attempted=$true;launcher_task=$launcherTask;adb_task=$adbTask;reason='system_headless_primary_exhausted'}
  try{
    foreach($task in @($adbTask,$launcherTask)){
      $t=Get-ScheduledTask -TaskName $task -ErrorAction Stop
      if(-not $t.Settings.Enabled){Enable-ScheduledTask -TaskName $task -ErrorAction Stop | Out-Null}
    }
    Start-ScheduledTask -TaskName $adbTask -ErrorAction SilentlyContinue
    Start-ScheduledTask -TaskName $launcherTask -ErrorAction Stop
    $deadline=(Get-Date).AddSeconds(150)
    do{
      Start-Sleep -Seconds 2
      $after=Probe 'memu'
      if($after.healthy){$fallback.ok=$true;$fallback.after=$after;return @{ok=$true;action='interactive_fallback_healthy';authority='interactive_fallback';cleanup=$cleanup;primary=@{ok=$false;stdout=$direct.stdout;stderr=$direct.stderr};fallback=$fallback;after=$after}}
    }while((Get-Date)-lt $deadline)
    $fallback.ok=$false;$fallback.after=Probe 'memu'
    return @{ok=$false;action='interactive_fallback_timeout';authority='none';cleanup=$cleanup;primary=@{ok=$false;stdout=$direct.stdout;stderr=$direct.stderr};fallback=$fallback;after=$fallback.after}
  }catch{
    $fallback.ok=$false;$fallback.error=$_.Exception.Message
    return @{ok=$false;action='interactive_fallback_failed';authority='none';cleanup=$cleanup;primary=@{ok=$false;stdout=$direct.stdout;stderr=$direct.stderr};fallback=$fallback;after=(Probe 'memu')}
  }finally{
    foreach($task in @($adbTask,$launcherTask)){Disable-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue | Out-Null}
  }
}
function RepairGuestAdbTcp{
  $m=MemuInfo
  if($m.state -ne 'running' -or -not $m.serial){return [ordered]@{ok=$false;attempted=$false;reason='backend_not_running';state=$m.state}}
  $boot=MemuGuest '/system/bin/getprop sys.boot_completed' 8
  $adbd=MemuGuest '/system/bin/getprop init.svc.adbd' 8
  $port=MemuGuest '/system/bin/getprop service.adb.tcp.port' 8
  $bootText=$boot.stdout.Trim();$adbdText=$adbd.stdout.Trim();$portText=$port.stdout.Trim()
  if(-not $boot.ok -or -not $adbd.ok -or $bootText -ne '1' -or $adbdText -ne 'running'){
    return [ordered]@{ok=$false;attempted=$true;reason='guest_not_ready';boot=$bootText;adbd=$adbdText;port=$portText}
  }
  if($portText -ne '5555'){
    [void](MemuGuest '/system/bin/setprop service.adb.tcp.port 5555' 8)
    [void](MemuGuest '/system/bin/setprop persist.adb.tcp.port 5555' 8)
    [void](MemuGuest '/system/bin/setprop ctl.restart adbd' 8)
    Start-Sleep -Seconds 4
  }
  $verifiedPort=(MemuGuest '/system/bin/getprop service.adb.tcp.port' 8).stdout.Trim()
  $verifiedAdbd=(MemuGuest '/system/bin/getprop init.svc.adbd' 8).stdout.Trim()
  [void](Adb @('disconnect',$m.serial) $null 7);[void](Adb @('connect',$m.serial) $null 8);Start-Sleep -Seconds 3
  $after=Probe 'memu'
  [ordered]@{ok=[bool]$after.healthy;attempted=$true;action='guest_adbd_tcp_repair';boot=$bootText;adbd=$verifiedAdbd;port=$verifiedPort;after=$after}
}
function Probe([string]$Kind){
  $m=MemuInfo
  if($Kind -eq 'physical'){$serial=$PhysicalSerial;$pkg='kwai.lite.video';$backend='physical_android';$backendState='external'}else{$serial=$m.serial;$pkg='com.kwai.video';$backend='memu_android';$backendState=$m.state}
  $devices=Devices;$ts=if($serial -and $devices.ContainsKey($serial)){$devices[$serial]}else{'missing'}
  $boot=$false;$installed=$false
  if($ts -eq 'device'){$b=Adb @('shell','getprop','sys.boot_completed') $serial 7;$boot=($b.ok -and $b.stdout.Trim() -eq '1');if($boot){$p=Adb @('shell','pm','path',$pkg) $serial 9;$installed=($p.ok -and $p.stdout -match 'package:')}}
  $healthy=($ts -eq 'device' -and $boot -and $installed)
  [ordered]@{executor=$backend;serial=$serial;backend_state=$backendState;transport=$ts;boot_completed=$boot;kwai_package=$pkg;package_installed=$installed;healthy=$healthy}
}
function RecoverTransport([string]$Kind,[switch]$MayStart,[switch]$MayReset){
  $mutex=$null;$lockTaken=$false
  if($Kind -eq 'memu'){
    try{
      $created=$false
      $mutex=New-Object System.Threading.Mutex($false,'Global\AntharesMEmuRecoveryAuthority',[ref]$created)
      $lockTaken=$mutex.WaitOne(5000)
      if(-not $lockTaken){return [ordered]@{ok=$false;action='recovery_busy';reason='another_anthares_runtime_recovery_holds_authority';after=(Probe $Kind)}}
    }catch{return [ordered]@{ok=$false;action='recovery_lock_failed';reason=$_.Exception.Message;after=(Probe $Kind)}}
  }
  try{
    $before=Probe $Kind
    if($before.healthy){return [ordered]@{ok=$true;action='already_healthy';before=$before;after=$before}}
    if($Kind -eq 'memu' -and $before.backend_state -ne 'running'){
      if(-not $MayStart){return [ordered]@{ok=$false;action='backend_start_not_authorized';before=$before;after=$before}}
      $start=StartMemuOfficial
      if(-not $start.ok){return [ordered]@{ok=$false;action='backend_start_failed';before=$before;after=(Probe $Kind);start=$start}}
    }
    [void](Adb @('start-server') $null 8)
    $serial=if($Kind -eq 'physical'){$PhysicalSerial}else{(MemuInfo).serial}
    if($serial){if($serial -match '^127\.0\.0\.1:'){[void](Adb @('disconnect',$serial) $null 7);[void](Adb @('connect',$serial) $null 8)}else{[void](Adb @('reconnect') $serial 8)}}
    $deadline=(Get-Date).AddSeconds(25)
    do{Start-Sleep -Milliseconds 800;$after=Probe $Kind;if($after.healthy){return [ordered]@{ok=$true;action='transport_recovered';before=$before;after=$after}}}while((Get-Date)-lt $deadline)
    if($Kind -eq 'memu'){$guestRepair=RepairGuestAdbTcp;if($guestRepair.ok){return [ordered]@{ok=$true;action='guest_adbd_tcp_recovered';before=$before;after=$guestRepair.after;guest_repair=$guestRepair}}}else{$guestRepair=$null}
    if($Kind -eq 'memu' -and $MayReset){[void](Run -File $Mgr -Arguments @('controlvm',$Vm,'reset') -Timeout 15);$deadline=(Get-Date).AddSeconds(45);do{Start-Sleep -Seconds 2;$after=Probe $Kind;if($after.healthy){return [ordered]@{ok=$true;action='backend_reset_recovered';before=$before;after=$after;guest_repair=$guestRepair}}}while((Get-Date)-lt $deadline)}
    [ordered]@{ok=$false;action='recovery_exhausted';before=$before;after=(Probe $Kind);guest_repair=$guestRepair}
  }finally{
    if($lockTaken -and $mutex){try{$mutex.ReleaseMutex()}catch{}}
    if($mutex){$mutex.Dispose()}
  }
}
function SelectExecutor{
  if($PublicationState -in @('STARTED','COMMITTING','UNCERTAIN')){return [ordered]@{ok=$false;selected=$null;reason='publication_state_blocks_failover';publication_state=$PublicationState}}
  $p=Probe 'physical'
  if(-not $p.healthy){$pr=RecoverTransport 'physical'}else{$pr=$null}
  $p2=Probe 'physical'
  if($p2.healthy){return [ordered]@{ok=$true;selected='physical_android';reason='primary_healthy';physical=$p2;recovery=$pr}}
  $m=Probe 'memu'
  if(-not $m.healthy){$mr=RecoverTransport 'memu' -MayStart:$AllowBackendStart -MayReset:$AllowBackendReset}else{$mr=$null}
  $m2=Probe 'memu'
  if($m2.healthy){return [ordered]@{ok=$true;selected='memu_android';reason='physical_unavailable_after_transport_recovery';physical=$p2;memu=$m2;recovery=$mr}}
  [ordered]@{ok=$false;selected=$null;reason='no_healthy_executor';physical=$p2;memu=$m2;recovery=$mr}
}
function ActiveProbe{
  if($Target -eq 'physical'){Probe 'physical'}elseif($Target -eq 'memu'){Probe 'memu'}else{$s=SelectExecutor;if($s.selected -eq 'physical_android'){Probe 'physical'}elseif($s.selected -eq 'memu_android'){Probe 'memu'}else{$null}}
}

function InvokeAgentCommand([string]$Cmd,[string]$Arg=''){
  $a=@('shell','am','broadcast','-a','us.anthares.agent.COMMAND','--es','cmd',$Cmd)
  if($Arg){$a+=@('--es','arg',$Arg)}
  Adb $a (MemuInfo).serial 10
}
function GetAgentSnapshot{
  $r=InvokeAgentCommand 'snapshot'
  if(-not $r.ok){return ''}
  $txt=[string]$r.stdout
  $m=[regex]::Match($txt,'data="([\s\S]*?)"\s*$')
  if($m.Success){return $m.Groups[1].Value}
  $txt
}
function GetKwaiIdentity{
  $h=ActiveProbe
  $expected='@lucasrosalem'
  if(-not $h -or -not $h.healthy){return [ordered]@{ok=$false;identity=$null;expected=$expected;reason='no_healthy_target'}}
  [void](Adb @('shell','monkey','-p',$h.kwai_package,'-c','android.intent.category.LAUNCHER','1') $h.serial 12)
  Start-Sleep -Seconds 2
  $fg=Adb @('shell','dumpsys','window','windows') $h.serial 10
  $fgLine=($fg.stdout -split "`r?`n"|Where-Object{$_ -match 'mCurrentFocus|mFocusedApp'}|Select-Object -First 1)
  $snap=GetAgentSnapshot
  $navigation='none'
  if($snap -notmatch [regex]::Escape($expected)){
    $click=InvokeAgentCommand 'click_id' 'id_home_bottom_tab_me'
    if($click.stdout -match 'OK'){$navigation='anthares_agent_profile_id';Start-Sleep -Seconds 3;$snap=GetAgentSnapshot}
  }
  if($snap -notmatch [regex]::Escape($expected)){
    [void](Adb @('shell','uiautomator','dump','/sdcard/anthares-window.xml') $h.serial 12)
    $u=Adb @('shell','cat','/sdcard/anthares-window.xml') $h.serial 10
    $xml=[string]$u.stdout
    if($xml -notmatch [regex]::Escape($expected)){
      $m=[regex]::Match($xml,'resource-id="com\.kwai\.video\.basis:id/id_home_bottom_tab_me"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
      if($m.Success){$x=[int](([int]$m.Groups[1].Value+[int]$m.Groups[3].Value)/2);$y=[int](([int]$m.Groups[2].Value+[int]$m.Groups[4].Value)/2);[void](Adb @('shell','input','tap',[string]$x,[string]$y) $h.serial 8);$navigation='semantic_profile_bounds';Start-Sleep -Seconds 3;[void](Adb @('shell','uiautomator','dump','/sdcard/anthares-window.xml') $h.serial 12);$u=Adb @('shell','cat','/sdcard/anthares-window.xml') $h.serial 10;$xml=[string]$u.stdout}
    }
    if($xml -match [regex]::Escape($expected)){$snap=$xml}
  }
  $identity=if($snap -match [regex]::Escape($expected)){$expected}else{$null}
  [ordered]@{ok=[bool]($identity -eq $expected -and $fgLine -match 'com\.kwai\.video');identity=$identity;expected=$expected;foreground=if($fgLine){$fgLine.Trim()}else{''};profile_marker_visible=[bool]($identity -eq $expected);navigation=$navigation}
}
switch($Command){
  'health'{$o=[ordered]@{ok=$true;physical=(Probe 'physical');memu=(Probe 'memu');policy=[ordered]@{priority=@('physical_android','memu_android');remote_android='experimental_only'}}}
  'select'{$o=SelectExecutor}
  'recover'{if($Target -eq 'auto'){$o=SelectExecutor}else{$o=RecoverTransport $Target -MayStart:$AllowBackendStart -MayReset:$AllowBackendReset}}
  'launch'{$h=ActiveProbe;if($h -and $h.healthy){$r=Adb @('shell','monkey','-p',$h.kwai_package,'-c','android.intent.category.LAUNCHER','1') $h.serial 12;$o=[ordered]@{ok=$r.ok;executor=$h.executor;serial=$h.serial;package=$h.kwai_package}}else{$o=[ordered]@{ok=$false;reason='no_healthy_target'}}}
  'foreground'{$h=ActiveProbe;if($h -and $h.healthy){$r=Adb @('shell','dumpsys','window','windows') $h.serial 10;$line=($r.stdout -split "`r?`n"|Where-Object{$_ -match 'mCurrentFocus|mFocusedApp'}|Select-Object -First 1);$o=[ordered]@{ok=$r.ok;executor=$h.executor;foreground=if($line){$line.Trim()}else{''}}}else{$o=[ordered]@{ok=$false;reason='no_healthy_target'}}}
  'identity'{$o=GetKwaiIdentity}
  'ui'{$h=ActiveProbe;if($h -and $h.healthy){[void](Adb @('shell','uiautomator','dump','/sdcard/anthares-window.xml') $h.serial 12);$r=Adb @('shell','cat','/sdcard/anthares-window.xml') $h.serial 10;$o=[ordered]@{ok=$r.ok;executor=$h.executor;xml=$r.stdout}}else{$o=[ordered]@{ok=$false;reason='no_healthy_target'}}}
}
Event $Command $o | ConvertTo-Json -Depth 12 -Compress

