param(
    [string]$Repository = 'UniversoAnthares/anthares-ara-queue',
    [string]$DeviceId = 'DESKTOP-FTDK0HP',
    [string]$WorkRoot = 'D:\AntharesWork\AntharesRemote',
    [int]$IntervalSeconds = 20,
    [int]$LeaseSeconds = 120
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2
$BridgeVersion = '2.1.0'
$StateDir = Join-Path $WorkRoot 'state'
$LogDir = Join-Path $WorkRoot 'logs'
$SecretDir = Join-Path $WorkRoot 'secrets'
$LedgerPath = Join-Path $StateDir 'ledger.json'
$HealthPath = Join-Path $StateDir 'health.json'
$GithubHealthPath = Join-Path $StateDir 'github-health.json'
$LegacyCredential = Join-Path $SecretDir 'github-queue-token.dpapi'
$MachineCredential = Join-Path $SecretDir 'github-queue-token.machine.b64'
$AllowedTypes = @('ping','system_info','process_list','service_status','file_stat','file_sha256','file_list','job_status')
New-Item -ItemType Directory -Force -Path $WorkRoot,$StateDir,$LogDir,$SecretDir | Out-Null

function Write-AtomicJson {
    param([string]$Path,[object]$Value,[int]$Depth=10)
    $tmp = "$Path.tmp.$PID.$([guid]::NewGuid().ToString('N'))"
    $json = $Value | ConvertTo-Json -Depth $Depth
    [IO.File]::WriteAllText($tmp,$json,(New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Write-Log {
    param([string]$Event,[string]$Status='info',[string]$JobId='',[string]$Message='')
    try {
        $today=(Get-Date).ToString('yyyyMMdd')
        $path=Join-Path $LogDir "github-queue-bridge-$today.log"
        if((Test-Path $path) -and (Get-Item $path).Length -gt 10485760){
            Move-Item $path "$path.$((Get-Date).ToString('HHmmss')).old" -Force
        }
        Get-ChildItem $LogDir -Filter 'github-queue-bridge-*.log*' -File -ErrorAction SilentlyContinue |
            Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-14)} | Remove-Item -Force -ErrorAction SilentlyContinue
        $safe=($Message -replace '[\r\n]+',' '); if($safe.Length -gt 1000){$safe=$safe.Substring(0,1000)}
        $line=[ordered]@{timestamp=(Get-Date).ToUniversalTime().ToString('o');transport='github';job_id=$JobId;event=$Event;status=$Status;message=$safe} | ConvertTo-Json -Compress
        Add-Content -LiteralPath $path -Value $line -Encoding UTF8
    } catch {}
}
function New-EmptyLedger {
    [ordered]@{version=1;fence_counter=0;jobs=[pscustomobject]@{}}
}
function Read-Ledger {
    if(-not(Test-Path $LedgerPath)){return (New-EmptyLedger)}
    try {
        $l=Get-Content $LedgerPath -Raw | ConvertFrom-Json
        if($null -eq $l.jobs){$l | Add-Member -NotePropertyName jobs -NotePropertyValue ([pscustomobject]@{})}
        if($null -eq $l.fence_counter){$l | Add-Member -NotePropertyName fence_counter -NotePropertyValue 0}
        return $l
    } catch {
        $bad="$LedgerPath.corrupt.$((Get-Date).ToString('yyyyMMddHHmmss'))"
        Copy-Item $LedgerPath $bad -Force -ErrorAction SilentlyContinue
        throw "ledger unreadable; backup=$bad"
    }
}
function Save-Ledger([object]$Ledger){ Write-AtomicJson -Path $LedgerPath -Value $Ledger -Depth 12 }
function Get-JobProp([object]$Jobs,[string]$Key){
    if($null -eq $Jobs){return $null}
    $p=$Jobs.PSObject.Properties[$Key]; if($null -eq $p){return $null}; return $p.Value
}
function Set-JobProp([object]$Jobs,[string]$Key,[object]$Value){
    $p=$Jobs.PSObject.Properties[$Key]
    if($null -eq $p){$Jobs | Add-Member -NotePropertyName $Key -NotePropertyValue $Value}else{$p.Value=$Value}
}
function Hash-Text([string]$Text){
    $sha=[Security.Cryptography.SHA256]::Create()
    try{return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLowerInvariant()} finally {$sha.Dispose()}
}
function Normalize-Result([object]$Value){
    $json=$Value | ConvertTo-Json -Depth 8 -Compress
    if($json.Length -gt 28000){$json=$json.Substring(0,28000)+'...TRUNCATED'}
    return $json
}
function Get-GhPath {
    $cmd=Get-Command gh -ErrorAction SilentlyContinue
    if($cmd){return $cmd.Source}
    $fixed='C:\Program Files\GitHub CLI\gh.exe'
    if(Test-Path $fixed){return $fixed}
    throw 'gh CLI required'
}
$Gh=Get-GhPath
function Invoke-Gh {
    param([string[]]$GhArgs,[switch]$IgnoreExit)
    $out=& $Gh @GhArgs 2>&1
    $code=$LASTEXITCODE
    if($code -ne 0 -and -not $IgnoreExit){throw "gh exit=${code}: $([string]::Join(' ',@($out)))"}
    return @($out)
}
function Ensure-GhAuth {
    $private=Invoke-Gh -GhArgs @('repo','view',$Repository,'--json','isPrivate','--jq','.isPrivate')
    if(([string]($private|Select-Object -First 1)).Trim() -ne 'true'){throw 'private repository required'}
}
function Ensure-Labels {
    $defs=@(
        @('ara-queued','ededed'),@('ara-leased','fbca04'),@('ara-running','1d76db'),
        @('ara-completed','0e8a16'),@('ara-failed','d73a4a'),@('ara-uncertain','b60205')
    )
    foreach($d in $defs){Invoke-Gh -GhArgs @('label','create',$d[0],'-R',$Repository,'--color',$d[1],'--force') -IgnoreExit | Out-Null}
}
function Set-IssueLabels {
    param([int]$Number,[string]$State)
    if([string]::IsNullOrWhiteSpace($State)){throw 'state label required'}
    Invoke-Gh -GhArgs @('api','--method','PUT',"repos/$Repository/issues/$Number/labels",'-f',"labels[]=$State",'--silent') | Out-Null
}
function Add-ResultComment {
    param([int]$Number,[string]$JobId,[string]$Status,[string]$ResultJson,[string]$ResultHash)
    $marker="<!-- ara-result:${JobId}:${ResultHash} -->"
    $comments=Invoke-Gh -GhArgs @('api',"repos/$Repository/issues/$Number/comments",'--paginate') -IgnoreExit
    $joined=[string]::Join("`n",@($comments))
    if($joined -match [regex]::Escape($marker)){return}
    $body="$marker`nARA result`n`n" + '```json' + "`n$ResultJson`n" + '```'
    if($body.Length -gt 32000){$body=$body.Substring(0,32000)}
    $tmp=Join-Path $StateDir ('comment-'+[guid]::NewGuid().ToString('N')+'.md')
    try{
        [IO.File]::WriteAllText($tmp,$body,(New-Object Text.UTF8Encoding($false)))
        Invoke-Gh -GhArgs @('issue','comment',"$Number",'-R',$Repository,'--body-file',$tmp) | Out-Null
    } finally {
        Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    }
}
function Parse-IssueJob {
    param([object]$Issue)
    $body=[string]$Issue.body
    $j=$body | ConvertFrom-Json -ErrorAction Stop
    if([string]::IsNullOrWhiteSpace([string]$j.device_id)){throw 'device_id required'}
    if($j.device_id -ne $DeviceId){throw 'device_id mismatch'}
    if([string]::IsNullOrWhiteSpace([string]$j.type)){throw 'type required'}
    if($AllowedTypes -notcontains [string]$j.type){throw "type not allowed: $($j.type)"}
    $jobId=[string]$j.job_id
    if([string]::IsNullOrWhiteSpace($jobId)){$jobId="github-issue-$($Issue.number)"}
    if($jobId -notmatch '^[A-Za-z0-9._:-]{1,128}$'){throw 'invalid job_id'}
    $idem=[string]$j.idempotency_key
    if([string]::IsNullOrWhiteSpace($idem)){$idem=$jobId}
    if($idem.Length -gt 160){throw 'idempotency_key too long'}
    $created=[DateTime]::UtcNow
    if($j.created_at){$created=[DateTime]::Parse([string]$j.created_at).ToUniversalTime()}
    if($created -gt [DateTime]::UtcNow.AddMinutes(5)){throw 'created_at in future'}
    if($j.expires_at){
        $exp=[DateTime]::Parse([string]$j.expires_at).ToUniversalTime()
        if($exp -lt [DateTime]::UtcNow){throw 'job expired'}
    }
    [pscustomobject]@{
        job_id=$jobId; idempotency_key=$idem; device_id=$DeviceId; type=[string]$j.type
        args=$j.args; created_at=$created.ToString('o'); source='github'; issue_number=[int]$Issue.number
    }
}
function Find-ByIdempotency([object]$Jobs,[string]$Key){
    foreach($p in $Jobs.PSObject.Properties){
        if([string]$p.Value.idempotency_key -eq $Key){return $p.Value}
    }
    return $null
}
function Acquire-Job {
    param([object]$Job)
    $mutex=[Threading.Mutex]::new($false,'Global\AntharesRemoteLedgerV1')
    $got=$false
    try{
        $got=$mutex.WaitOne(15000); if(-not $got){throw 'ledger lock timeout'}
        $l=Read-Ledger
        $existing=Get-JobProp $l.jobs $Job.job_id
        if($null -eq $existing){$existing=Find-ByIdempotency $l.jobs $Job.idempotency_key}
        if($null -ne $existing){
            if([string]$existing.status -eq 'completed' -or [string]$existing.status -eq 'failed'){
                return [pscustomobject]@{action='cached';record=$existing;lease_token=$null}
            }
            $until=[DateTime]::MinValue
            if($existing.lease_until){try{$until=[DateTime]::Parse([string]$existing.lease_until).ToUniversalTime()}catch{}}
            if(($existing.status -eq 'leased' -or $existing.status -eq 'running') -and $until -gt [DateTime]::UtcNow){
                return [pscustomobject]@{action='busy';record=$existing;lease_token=$null}
            }
        }
        $l.fence_counter=[int64]$l.fence_counter+1
        $token=[guid]::NewGuid().ToString('N')
        $now=[DateTime]::UtcNow
        $attempt=1
        if($null -ne $existing -and $existing.attempt){$attempt=[int]$existing.attempt+1}
        $rec=[ordered]@{
            job_id=$Job.job_id; idempotency_key=$Job.idempotency_key; transport=$Job.source; issue_number=$Job.issue_number
            type=$Job.type; args=$Job.args; status='leased'; created_at=$Job.created_at; leased_at=$now.ToString('o')
            started_at=$null; completed_at=$null; result=$null; result_hash=$null; attempt=$attempt; owner="${DeviceId}:github"
            lease_token=$token; fencing_token=[int64]$l.fence_counter; lease_until=$now.AddSeconds($LeaseSeconds).ToString('o')
        }
        Set-JobProp $l.jobs $Job.job_id ([pscustomobject]$rec)
        Save-Ledger $l
        return [pscustomobject]@{action='execute';record=([pscustomobject]$rec);lease_token=$token}
    } finally {if($got){try{$mutex.ReleaseMutex()}catch{}};$mutex.Dispose()}
}
function Mark-Running {
    param([string]$JobId,[string]$LeaseToken)
    $mutex=[Threading.Mutex]::new($false,'Global\AntharesRemoteLedgerV1');$got=$false
    try{$got=$mutex.WaitOne(15000);if(-not $got){throw 'ledger lock timeout'};$l=Read-Ledger;$r=Get-JobProp $l.jobs $JobId
        if($null -eq $r -or [string]$r.lease_token -ne $LeaseToken){throw 'fencing rejection at start'}
        $r.status='running';$r.started_at=[DateTime]::UtcNow.ToString('o');$r.lease_until=[DateTime]::UtcNow.AddSeconds($LeaseSeconds).ToString('o');Save-Ledger $l
    } finally {if($got){try{$mutex.ReleaseMutex()}catch{}};$mutex.Dispose()}
}
function Complete-Job {
    param([string]$JobId,[string]$LeaseToken,[string]$Status,[string]$ResultJson)
    $mutex=[Threading.Mutex]::new($false,'Global\AntharesRemoteLedgerV1');$got=$false
    try{$got=$mutex.WaitOne(15000);if(-not $got){throw 'ledger lock timeout'};$l=Read-Ledger;$r=Get-JobProp $l.jobs $JobId
        if($null -eq $r -or [string]$r.lease_token -ne $LeaseToken){throw 'fencing rejection at completion'}
        $r.status=$Status;$r.completed_at=[DateTime]::UtcNow.ToString('o');$r.result=$ResultJson;$r.result_hash=Hash-Text $ResultJson;$r.lease_until=$null;Save-Ledger $l;return $r
    } finally {if($got){try{$mutex.ReleaseMutex()}catch{}};$mutex.Dispose()}
}
function Assert-Path([string]$Path){
    if([string]::IsNullOrWhiteSpace($Path)){throw 'path required'}
    $full=[IO.Path]::GetFullPath($Path)
    $allowed=[IO.Path]::GetFullPath('D:\AntharesWork')
    if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'path outside D:\AntharesWork denied'}
    return $full
}
function Invoke-Handler {
    param([object]$Job)
    $a=$Job.args
    switch($Job.type){
        'ping' { return [ordered]@{ok=$true;output='pong';device_id=$DeviceId;version=$BridgeVersion} }
        'system_info' {
            return [ordered]@{ok=$true;computer=[Environment]::MachineName;user=[Environment]::UserName;os=[Environment]::OSVersion.VersionString;version=[Environment]::OSVersion.Version.ToString();ps=$PSVersionTable.PSVersion.ToString();utc_now=[DateTime]::UtcNow.ToString('o')}
        }
        'process_list' {
            $items=Get-CimInstance Win32_Process | Select-Object -First 200 ProcessId,ParentProcessId,Name,CreationDate,CommandLine
            return [ordered]@{ok=$true;count=@($items).Count;processes=@($items)}
        }
        'service_status' {
            $name=[string]$a.name;if([string]::IsNullOrWhiteSpace($name)){throw 'args.name required'}
            $s=Get-Service -Name $name -ErrorAction Stop
            return [ordered]@{ok=$true;name=$s.Name;display_name=$s.DisplayName;status=[string]$s.Status;start_type=[string]$s.StartType}
        }
        'file_stat' {
            $path=Assert-Path ([string]$a.path);$x=Get-Item -LiteralPath $path -Force -ErrorAction Stop
            return [ordered]@{ok=$true;path=$x.FullName;exists=$true;is_directory=$x.PSIsContainer;length=if($x.PSIsContainer){$null}else{$x.Length};last_write=$x.LastWriteTimeUtc.ToString('o')}
        }
        'file_sha256' {
            $path=Assert-Path ([string]$a.path);$h=Get-FileHash -LiteralPath $path -Algorithm SHA256
            return [ordered]@{ok=$true;path=$path;sha256=$h.Hash}
        }
        'file_list' {
            $path=Assert-Path ([string]$a.path);$items=Get-ChildItem -LiteralPath $path -Force -ErrorAction Stop | Select-Object -First 200 Name,FullName,Length,LastWriteTime,Mode
            return [ordered]@{ok=$true;path=$path;count=@($items).Count;items=@($items)}
        }
        'job_status' {
            $target=[string]$a.job_id;if([string]::IsNullOrWhiteSpace($target)){throw 'args.job_id required'}
            $l=Read-Ledger;$r=Get-JobProp $l.jobs $target
            return [ordered]@{ok=$true;job_id=$target;found=($null -ne $r);record=$r}
        }
        default {throw 'handler missing'}
    }
}
function Update-Health([bool]$GithubHealthy,[string]$LastError='',[string]$LastJobId=''){
    $now=[DateTime]::UtcNow.ToString('o')
    $gh=[ordered]@{last_poll=$now;last_success=if($GithubHealthy){$now}else{$null};last_error=$LastError;last_job_id=$LastJobId;consecutive_failures=0}
    if(Test-Path $GithubHealthPath){try{$old=Get-Content $GithubHealthPath -Raw|ConvertFrom-Json;if(-not $GithubHealthy){$gh.consecutive_failures=[int]$old.consecutive_failures+1}elseif($old.last_success){$gh.last_success=[string]$old.last_success}}catch{}}
    if($GithubHealthy){$gh.last_success=$now;$gh.consecutive_failures=0}
    Write-AtomicJson $GithubHealthPath $gh 6
    $ledgerOk=$true;try{$null=Read-Ledger}catch{$ledgerOk=$false}
    $health=[ordered]@{updated_at=$now;version=$BridgeVersion;device_id=$DeviceId;control_transport='unknown';github_transport=if($GithubHealthy){'healthy'}else{'unhealthy'};executor='healthy';ledger=if($ledgerOk){'healthy'}else{'unhealthy'};scheduled_task='unknown'}
    Write-AtomicJson $HealthPath $health 6
}
function Process-Issue([object]$Issue){
    $job=$null
    try{
        $job=Parse-IssueJob $Issue
        Write-Log 'job_seen' 'info' $job.job_id "issue=$($Issue.number);type=$($job.type)"
        $acq=Acquire-Job $job
        if($acq.action -eq 'busy'){return}
        if($acq.action -eq 'cached'){
            $r=$acq.record
            $res=[string]$r.result
            if([string]::IsNullOrWhiteSpace($res)){$res='{"ok":false,"error":"cached result unavailable"}'}
            try{
                Add-ResultComment -Number $Issue.number -JobId $job.job_id -Status ([string]$r.status) -ResultJson $res -ResultHash ([string]$r.result_hash)
                Set-IssueLabels $Issue.number $(if($r.status -eq 'completed'){'ara-completed'}else{'ara-failed'})
                Write-Log 'job_deduplicated' 'info' $job.job_id "issue=$($Issue.number)"
            }catch{
                Write-Log 'reconcile_error' 'error' $job.job_id ($_.Exception.Message+' | '+$_.ScriptStackTrace)
                try{Set-IssueLabels $Issue.number 'ara-queued'}catch{}
            }
            return
        }
        try{Set-IssueLabels $Issue.number 'ara-leased'}catch{Write-Log 'label_error' 'error' $job.job_id $_.Exception.Message}
        Mark-Running $job.job_id $acq.lease_token
        try{Set-IssueLabels $Issue.number 'ara-running'}catch{Write-Log 'label_error' 'error' $job.job_id $_.Exception.Message}
        $json=$null
$rec=$null
        try{
            $value=Invoke-Handler $job
            $json=Normalize-Result $value
            $rec=Complete-Job $job.job_id $acq.lease_token 'completed' $json
        }catch{
            $execMessage=$_.Exception.Message
            $execTrace=$_.ScriptStackTrace
            $json=Normalize-Result ([ordered]@{ok=$false;error=$execMessage;type=$job.type})
            try{$rec=Complete-Job $job.job_id $acq.lease_token 'failed' $json;$hash=[string]$rec.result_hash}catch{$hash=Hash-Text $json}
            try{
                Add-ResultComment $Issue.number $job.job_id 'failed' $json $hash
                Set-IssueLabels $Issue.number 'ara-failed'
            }catch{
                Write-Log 'result_publish_error' 'error' $job.job_id ($_.Exception.Message+' | '+$_.ScriptStackTrace)
                try{Set-IssueLabels $Issue.number 'ara-queued'}catch{}
            }
            Write-Log 'job_failed' 'error' $job.job_id ($execMessage+' | '+$execTrace)
            return
        }
        try{
            Add-ResultComment $Issue.number $job.job_id 'completed' $json ([string]$rec.result_hash)
            Set-IssueLabels $Issue.number 'ara-completed'
            Write-Log 'job_completed' 'ok' $job.job_id "issue=$($Issue.number)"
        }catch{
            Write-Log 'result_publish_error' 'error' $job.job_id ($_.Exception.Message+' | '+$_.ScriptStackTrace)
            try{Set-IssueLabels $Issue.number 'ara-queued'}catch{}
        }
    }catch{
        $outerMessage=$_.Exception.Message
        $outerTrace=$_.ScriptStackTrace
        $jid=if($null-ne$job){$job.job_id}else{"github-issue-$($Issue.number)"}
        Write-Log 'job_rejected' 'error' $jid ($outerMessage+' | '+$outerTrace)
        $json=Normalize-Result ([ordered]@{ok=$false;error=$outerMessage})
        try{
            Set-IssueLabels $Issue.number 'ara-failed'
            Add-ResultComment $Issue.number $jid 'failed' $json (Hash-Text $json)
        }catch{Write-Log 'rejection_publish_error' 'error' $jid $_.Exception.Message}
    }
}
$created=$false
$bridgeMutex=[Threading.Mutex]::new($true,'Global\AntharesGithubQueueBridgeV2',[ref]$created)
if(-not $created){Write-Log 'startup' 'info' '' 'duplicate bridge suppressed';exit 0}
try{
    Ensure-GhAuth
    Ensure-Labels
    Write-Log 'startup' 'ok' '' "bridge=$BridgeVersion"
    while($true){
        try{
            $raw=Invoke-Gh -GhArgs @('api',"repos/$Repository/issues?state=open&labels=ara-queued&per_page=50")
            $parsedIssues=([string]::Join("`n",@($raw)))|ConvertFrom-Json
            $issues=@(); foreach($entry in $parsedIssues){$issues += $entry}
            foreach($i in @($issues)){
                if($null -eq $i){continue}
                if($i.PSObject.Properties['pull_request']){continue}
                $userProp=$i.PSObject.Properties['user']
                $numberProp=$i.PSObject.Properties['number']
                if($null -eq $userProp -or $null -eq $numberProp){Write-Log 'poll_item_skipped' 'error' '' 'GitHub issue object missing required properties';continue}
                $loginProp=$userProp.Value.PSObject.Properties['login']
                if($null -eq $loginProp -or [string]$loginProp.Value -ne 'UniversoAnthares'){Write-Log 'job_rejected' 'error' ('github-issue-'+[string]$numberProp.Value) 'unauthorized issue author';continue}
                Process-Issue $i
            }
            Update-Health $true '' ''
        } catch {
            Update-Health $false $_.Exception.Message ''
            Write-Log 'poll_error' 'error' '' ($_.Exception.Message+' | '+$_.ScriptStackTrace)
        }
        Start-Sleep -Seconds ([Math]::Max(10,$IntervalSeconds))
    }
} finally {
    try{$bridgeMutex.ReleaseMutex()}catch{}
    $bridgeMutex.Dispose()
}
