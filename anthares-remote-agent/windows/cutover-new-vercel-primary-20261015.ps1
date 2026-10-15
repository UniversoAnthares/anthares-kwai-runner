$ErrorActionPreference='Stop'
$root='C:\ProgramData\AntharesRemoteAgent'
$p=Join-Path $root 'run-agent-system-supervisor.ps1'
if(-not (Test-Path $p)){throw 'supervisor missing'}
$b=$p+'.pre-new-vercel-'+(Get-Date -Format 'yyyyMMddHHmmss')+'.bak'
Copy-Item $p $b -Force
$lines=Get-Content -LiteralPath $p
$found=$false
$new=@()
foreach($line in $lines){
  if($line.StartsWith('$httpControl=')){
    $new += '$httpControl=''https://anthares-remote-primary.vercel.app'''
    $found=$true
  }else{
    $new += $line
  }
}
if(-not $found){throw 'httpControl line not found'}
Set-Content -LiteralPath $p -Value $new -Encoding UTF8
$check=(Get-Content $p | Where-Object {$_.StartsWith('$httpControl=')} | Select-Object -First 1)
if($check -ne '$httpControl=''https://anthares-remote-primary.vercel.app'''){throw ('replace verify failed: '+$check)}

$restart=Join-Path $root 'restart-new-vercel-primary-once.ps1'
@'
$ErrorActionPreference='Continue'
Start-Sleep -Seconds 12
Stop-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName 'Anthares Remote Agent SYSTEM' -ErrorAction Stop
Start-Sleep -Seconds 8
@{restarted=$true;at=(Get-Date).ToUniversalTime().ToString('o')}|ConvertTo-Json -Compress|Set-Content 'C:\ProgramData\AntharesRemoteAgent\new-vercel-primary-restart-result.json' -Encoding UTF8
Unregister-ScheduledTask -TaskName 'Anthares Remote Agent New Vercel Restart' -Confirm:$false -ErrorAction SilentlyContinue
'@ | Set-Content -LiteralPath $restart -Encoding UTF8
$action=New-ScheduledTaskAction -Execute 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$restart+'"') -WorkingDirectory $root
$trigger=New-ScheduledTaskTrigger -Once -At ((Get-Date).AddSeconds(18))
$principal=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 3)
Register-ScheduledTask -TaskName 'Anthares Remote Agent New Vercel Restart' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force|Out-Null
[pscustomobject]@{
  ok=$true
  line=$check
  backup=$b
  sha=(Get-FileHash $p -Algorithm SHA256).Hash
  restart_at=$trigger.StartBoundary
}|ConvertTo-Json -Compress
