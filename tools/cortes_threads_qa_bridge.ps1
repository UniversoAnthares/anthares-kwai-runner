$ErrorActionPreference='Stop'
$root='D:\AntharsWork\cortes-social-browser-20261020'
$stateFile=Join-Path $root 'threads-continuity-state.json'
$ledgerFile=Join-Path $root 'threads-qa-notification-state.json'
$audit=Join-Path $root 'threads-qa-notification.log'
try {
 if(!(Test-Path $stateFile)){exit 0}
 $state=Get-Content $stateFile -Raw -Encoding UTF8|ConvertFrom-Json
 if(!$state.problems -or @($state.problems).Count -eq 0){exit 0}
 $known=$null
 if(Test-Path $ledgerFile){try{$known=Get-Content $ledgerFile -Raw -Encoding UTF8|ConvertFrom-Json}catch{}}
 $warnings=(@($state.problems)|Sort-Object -Unique) -join '|'
 $id=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($warnings)).TrimEnd('=')
 $last=if($known -and $known.fingerprint -eq $id){[DateTime]::Parse($known.sent_at).ToUniversalTime()}else{[DateTime]'2000-01-01T00:00:00Z'}
 if(([DateTime]::UtcNow-$last).TotalMinutes -lt 120){exit 0}
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $token=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if(!$token){throw 'QA_ISSUE_AUTH_UNAVAILABLE'}
 $headers=@{Authorization='Bearer '+$token;Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28';'User-Agent'='Anthares-Threads-QA-Watchdog'}
 $severity=if(@($state.problems|Where-Object{$_ -in @('PUBLICATION_PROGRESS_STALLED','SCHEDULER_NO_HEARTBEAT','RECURRENT_PUBLICATION_ERRORS')} ).Count -gt 0){'P0'}else{'P1'}
 $problems=(@($state.problems) -join ', ')
 $body="[QA $severity][Threads][CORTES] Falha detectada pelo watchdog do Threads. Problemas: $problems. Confirmadas hoje: $($state.confirmed_today); pendentes: $($state.pending_count); incertas: $($state.uncertain_count). Horario UTC: $([DateTime]::UtcNow.ToString('o')). Exigir correcao do codigo e reconciliacao antes de repetir envios com estado UNCERTAIN. Origem: threads-continuity-state.json. Limite diario: 100."
 $payload=@{body=$body}|ConvertTo-Json -Compress
 Invoke-RestMethod -Uri 'https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments' -Headers $headers -Method POST -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 25|Out-Null
 $new=@{sent_at=[DateTime]::UtcNow.ToString('o');fingerprint=$id;severity=$severity}
 [IO.File]::WriteAllText($ledgerFile,($new|ConvertTo-Json -Compress),[Text.UTF8Encoding]::new($false))
 [IO.File]::AppendAllText($audit,([DateTime]::UtcNow.ToString('o')+' NOTIFIED '+$severity+' '+$problems+[Environment]::NewLine))
}catch{
 [IO.File]::AppendAllText($audit,([DateTime]::UtcNow.ToString('o')+' ERROR '+$_.Exception.GetType().Name+[Environment]::NewLine))
 exit 1
}