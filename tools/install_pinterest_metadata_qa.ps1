# Register one hidden QA worker; can repair 404 and missing editorial metadata.
param([string]$RepoPath=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference='Stop'
$name='CORTES-Pinterest-QA-24h-Editorial'
$script=Join-Path $RepoPath 'tools\run_pinterest_metadata_qa.ps1'
if(-not(Test-Path $script)){throw 'PINTEREST_QA_WRAPPER_MISSING'}
# Provision a dedicated reproducible ASR runtime before enabling scheduled QA.
$qaDeps=Join-Path $RepoPath '.pinterest-qa-deps'
if(-not(Test-Path (Join-Path $qaDeps 'faster_whisper\__init__.py'))){
    & py -3 -m pip install --disable-pip-version-check --no-input --no-warn-script-location --target $qaDeps 'faster-whisper==1.2.1'
    if($LASTEXITCODE -ne 0 -or -not(Test-Path (Join-Path $qaDeps 'faster_whisper\__init__.py'))){
        throw 'PINTEREST_QA_ASR_DEPENDENCY_INSTALL_FAILED'
    }
}
$exe=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arguments='-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "'+$script+'"'
$action=New-ScheduledTaskAction -Execute $exe -Argument $arguments -WorkingDirectory $RepoPath
$trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 3) -RepetitionDuration (New-TimeSpan -Days 365)
$settings=New-ScheduledTaskSettingsSet -Hidden -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 7) -MultipleInstances IgnoreNew
$principal=New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Pinterest: every 3m QA 404 deadline and transcript metadata repair, no publishing' -Force|Out-Null
Write-Output 'PINTEREST_QA_SCHEDULED'
