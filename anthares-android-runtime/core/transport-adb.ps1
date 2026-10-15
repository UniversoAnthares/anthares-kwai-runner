Set-StrictMode -Version Latest
$script:AdbServerPort=if($env:ANTHARES_ADB_SERVER_PORT){[int]$env:ANTHARES_ADB_SERVER_PORT}else{5043}
function ConvertTo-AntharesProcessArgument {
    param([AllowNull()][string]$Value)
    if($null -eq $Value){return '""'}
    if($Value -notmatch '[\s"]'){return $Value}
    return '"'+(($Value -replace '(\\*)"','$1$1\"') -replace '(\\+)$','$1$1')+'"'
}
function Invoke-AntharesProcess {
    param([string]$File,[string[]]$Args,[int]$TimeoutMs=8000)
    $clean=@($Args | Where-Object {$_ -ne $null -and [string]$_ -ne ''})
    $psi=New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName=$File
    $psi.Arguments=(($clean | ForEach-Object {ConvertTo-AntharesProcessArgument ([string]$_)}) -join ' ')
    $psi.UseShellExecute=$false
    $psi.CreateNoWindow=$true
    $psi.RedirectStandardOutput=$true
    $psi.RedirectStandardError=$true
    $p=New-Object System.Diagnostics.Process
    $p.StartInfo=$psi
    try {
        if(-not $p.Start()){return [ordered]@{ok=$false;timeout=$false;exit_code=$null;stdout='';stderr='process_start_failed'}}
        if(-not $p.WaitForExit($TimeoutMs)){
            try{$p.Kill()}catch{}
            return [ordered]@{ok=$false;timeout=$true;exit_code=$null;stdout='';stderr='process_timeout'}
        }
        $stdout=$p.StandardOutput.ReadToEnd()
        $stderr=$p.StandardError.ReadToEnd()
        return [ordered]@{ok=($p.ExitCode -eq 0);timeout=$false;exit_code=$p.ExitCode;stdout=$stdout;stderr=$stderr}
    } catch {
        return [ordered]@{ok=$false;timeout=$false;exit_code=$null;stdout='';stderr=$_.Exception.Message}
    } finally {$p.Dispose()}
}
function Invoke-AntharesAdb {
    param([string]$Adb,[string[]]$Args,[int]$TimeoutMs=8000,[int]$ServerPort=$script:AdbServerPort)
    try {
        $lines = & $Adb -P ([string]$ServerPort) @Args 2>&1
        $code = $LASTEXITCODE
        $text = (($lines | ForEach-Object {[string]$_}) -join "`r`n")
        return [ordered]@{ok=($code -eq 0);timeout=$false;exit_code=$code;stdout=$text;stderr=''}
    } catch {
        return [ordered]@{ok=$false;timeout=$false;exit_code=$null;stdout='';stderr=$_.Exception.Message}
    }
}
function Get-AdbDevices {
    param([string]$Adb,[int]$ServerPort=$script:AdbServerPort)
    $r=Invoke-AntharesAdb -Adb $Adb -Args @('devices','-l') -TimeoutMs 5000 -ServerPort $ServerPort
    $m=[ordered]@{}
    if($r.stdout){foreach($line in ($r.stdout -split "`r?`n" | Select-Object -Skip 1)){if($line -match '^(\S+)\s+(device|offline|unauthorized)\b'){$m[$matches[1]]=$matches[2]}}}
    [ordered]@{ok=$r.ok;devices=$m;raw=$r;server_port=$ServerPort}
}
