param(
  [ValidateSet('health','select','recover','launch','foreground','ui')][string]$Command='health',
  [ValidateSet('auto','physical','memu')][string]$Target='auto',
  [ValidateSet('IDLE','LEASED','STARTED','COMMITTING','UNCERTAIN','VERIFIED')][string]$PublicationState='IDLE',
  [switch]$AllowBackendStart,
  [switch]$AllowBackendReset
)
$ErrorActionPreference='Stop'
$Root='C:\ProgramData\AntharesAndroidRuntime'
$Adb='D:\Program Files\Microvirt\MEmu\adb.exe'
$Mgr='D:\Program Files\Microvirt\MEmuHyperv\MEmuManage.exe'
$Memuc='D:\Program Files\Microvirt\MEmu\memuc.exe'
$Vm='MEmu_4'
$VmIndex='4'
$PhysicalSerial=if($env:ANTHARES_PHYSICAL_ADB_SERIAL){$env:ANTHARES_PHYSICAL_ADB_SERIAL}else{'993fce720408'}
New-Item -ItemType Directory -Force -Path $Root | Out-Null

function Run([string]$File,[string[]]$Args,[int]$Timeout=12){
  $psi=New-Object Diagnostics.ProcessStartInfo
  $psi.FileName=$File;$psi.UseShellExecute=$false;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true
  $psi.Arguments=(($Args|ForEach-Object{if($_ -match '\s'){ '"'+$_+'"' }else{$_}})-join ' ')
  $p=New-Object Diagnostics.Process;$p.StartInfo=$psi
  try{[void]$p.Start();$o=$p.StandardOutput.ReadToEndAsync();$e=$p.StandardError.ReadToEndAsync();if(-not $p.WaitForExit($Timeout*1000)){try{$p.Kill()}catch{};return @{ok=$false;timeout=$true;stdout='';stderr='timeout'}};@{ok=($p.ExitCode -eq 0);code=$p.ExitCode;stdout=$o.Result;stderr=$e.Result}}catch{@{ok=$false;code=$null;stdout='';stderr=$_.Exception.Message}}finally{if($p){$p.Dispose()}}
}
function StartMemuOfficial{
  $old=$env:__COMPAT_LAYER
  try{$env:__COMPAT_LAYER='RunAsInvoker';Run $Memuc @('start','-i',$VmIndex) 35}finally{$env:__COMPAT_LAYER=$old}
}
function Event([string]$Op,$Data){
  $row=[ordered]@{timestamp=(Get-Date).ToUniversalTime().ToString('o');operation=$Op;data=$Data}
  ($row|ConvertTo-Json -Depth 12 -Compress)|Add-Content -Encoding UTF8 (Join-Path $Root 'events.jsonl')
  $row|ConvertTo-Json -Depth 12|Set-Content -Encoding UTF8 (Join-Path $Root 'state.json')
  $Data
}
function Adb([string[]]$Args,[string]$Serial=$null,[int]$Timeout=10){$a=@();if($Serial){$a+=@('-s',$Serial)};$a+=$Args;Run $Adb $a $Timeout}
function Devices{
  $r=Adb @('devices','-l');$d=@{}
  foreach($line in (($r.stdout -split "`r?`n")|Select-Object -Skip 1)){$p=$line.Trim() -split '\s+';if($p.Count -ge 2){$d[$p[0]]=$p[1]}}
  $d
}
function MemuInfo{
  $txt=(& $Mgr showvminfo $Vm --machinereadable 2>$null|Out-String);$state='unknown';$serial=$null
  if($txt -match '(?m)^VMState="([^"]+)"'){$state=$Matches[1]}
  if($txt -match 'Forwarding\(\d+\)="ADB,tcp,127\.0\.0\.1,(\d+),'){$serial='127.0.0.1:'+$Matches[1]}
  [ordered]@{state=$state;serial=$serial}
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
  $before=Probe $Kind
  if($before.healthy){return [ordered]@{ok=$true;action='already_healthy';before=$before;after=$before}}
  if($Kind -eq 'memu' -and $before.backend_state -ne 'running'){
    if(-not $MayStart){return [ordered]@{ok=$false;action='backend_start_not_authorized';before=$before;after=$before}}
    $start=StartMemuOfficial
    if(-not $start.ok){return [ordered]@{ok=$false;action='backend_start_failed';before=$before;after=(Probe $Kind);start=$start}}
  }
  [void](Adb @('start-server') $null 8)
  $serial=if($Kind -eq 'physical'){$PhysicalSerial}else{(MemuInfo).serial}
  if($serial){
    if($serial -match '^127\.0\.0\.1:'){[void](Adb @('disconnect',$serial) $null 7);[void](Adb @('connect',$serial) $null 8)}else{[void](Adb @('reconnect') $serial 8)}
  }
  $deadline=(Get-Date).AddSeconds(25)
  do{Start-Sleep -Milliseconds 800;$after=Probe $Kind;if($after.healthy){return [ordered]@{ok=$true;action='transport_recovered';before=$before;after=$after}}}while((Get-Date)-lt $deadline)
  if($Kind -eq 'memu' -and $MayReset){
    [void](Run $Mgr @('controlvm',$Vm,'reset') 15);$deadline=(Get-Date).AddSeconds(45)
    do{Start-Sleep -Seconds 2;$after=Probe $Kind;if($after.healthy){return [ordered]@{ok=$true;action='backend_reset_recovered';before=$before;after=$after}}}while((Get-Date)-lt $deadline)
  }
  [ordered]@{ok=$false;action='recovery_exhausted';before=$before;after=(Probe $Kind)}
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

switch($Command){
  'health'{$o=[ordered]@{ok=$true;physical=(Probe 'physical');memu=(Probe 'memu');policy=[ordered]@{priority=@('physical_android','memu_android');remote_android='experimental_only'}}}
  'select'{$o=SelectExecutor}
  'recover'{if($Target -eq 'auto'){$o=SelectExecutor}else{$o=RecoverTransport $Target -MayStart:$AllowBackendStart -MayReset:$AllowBackendReset}}
  'launch'{$h=ActiveProbe;if($h -and $h.healthy){$r=Adb @('shell','monkey','-p',$h.kwai_package,'-c','android.intent.category.LAUNCHER','1') $h.serial 12;$o=[ordered]@{ok=$r.ok;executor=$h.executor;serial=$h.serial;package=$h.kwai_package}}else{$o=[ordered]@{ok=$false;reason='no_healthy_target'}}}
  'foreground'{$h=ActiveProbe;if($h -and $h.healthy){$r=Adb @('shell','dumpsys','window','windows') $h.serial 10;$line=($r.stdout -split "`r?`n"|Where-Object{$_ -match 'mCurrentFocus|mFocusedApp'}|Select-Object -First 1);$o=[ordered]@{ok=$r.ok;executor=$h.executor;foreground=if($line){$line.Trim()}else{''}}}else{$o=[ordered]@{ok=$false;reason='no_healthy_target'}}}
  'ui'{$h=ActiveProbe;if($h -and $h.healthy){[void](Adb @('shell','uiautomator','dump','/sdcard/anthares-window.xml') $h.serial 12);$r=Adb @('shell','cat','/sdcard/anthares-window.xml') $h.serial 10;$o=[ordered]@{ok=$r.ok;executor=$h.executor;xml=$r.stdout}}else{$o=[ordered]@{ok=$false;reason='no_healthy_target'}}}
}
Event $Command $o | ConvertTo-Json -Depth 12 -Compress
