Set-StrictMode -Version Latest
function Invoke-AntharesProcess {
    param([string]$File,[string[]]$Args,[int]$TimeoutMs=8000)
    $tmp=[IO.Path]::GetTempFileName(); $err=[IO.Path]::GetTempFileName()
    try {
        $clean=@($Args | Where-Object {$_ -ne $null -and [string]$_ -ne ''})
        if($clean.Count -gt 0){$p=Start-Process -FilePath $File -ArgumentList $clean -WindowStyle Hidden -PassThru -RedirectStandardOutput $tmp -RedirectStandardError $err}
        else{$p=Start-Process -FilePath $File -WindowStyle Hidden -PassThru -RedirectStandardOutput $tmp -RedirectStandardError $err}
        if(-not $p.WaitForExit($TimeoutMs)){
            try{$p.Kill()}catch{}
            return [ordered]@{ok=$false;timeout=$true;exit_code=$null;stdout=(Get-Content $tmp -Raw -ErrorAction SilentlyContinue);stderr=(Get-Content $err -Raw -ErrorAction SilentlyContinue)}
        }
        return [ordered]@{ok=($p.ExitCode -eq 0);timeout=$false;exit_code=$p.ExitCode;stdout=(Get-Content $tmp -Raw -ErrorAction SilentlyContinue);stderr=(Get-Content $err -Raw -ErrorAction SilentlyContinue)}
    } finally {Remove-Item $tmp,$err -Force -ErrorAction SilentlyContinue}
}
function Invoke-AntharesAdb {
    param([string]$Adb,[string[]]$Args,[int]$TimeoutMs=8000)
    Invoke-AntharesProcess -File $Adb -Args $Args -TimeoutMs $TimeoutMs
}
function Get-AdbDevices {
    param([string]$Adb)
    $r=Invoke-AntharesAdb $Adb @('devices','-l') 5000
    $m=[ordered]@{}
    if($r.stdout){foreach($line in ($r.stdout -split "`r?`n" | Select-Object -Skip 1)){if($line -match '^(\S+)\s+(device|offline|unauthorized)\b'){$m[$matches[1]]=$matches[2]}}}
    [ordered]@{ok=$r.ok;devices=$m;raw=$r}
}
