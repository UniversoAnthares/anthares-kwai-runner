# Anthares Remote / SYSTEM quota-cancel standby. No third-party executor and no dispatch.
# Requires private DPAPI secrets and local nonsecret config; otherwise fail closed.
[CmdletBinding()]
param([string]$Root='D:\AntharesWork\AntharesRemote')
$ErrorActionPreference='Stop'
$Controller='https://anthares-ci-quota-controller.vercel.app/api/provider-cancel'
$Repo='UniversoAnthares/anthares-kwai-runner'
$SecretDir=Join-Path $Root 'secrets'
$StateDir=Join-Path $Root 'state'
$QuotaCodes=@('ci_quota_exceeded','quota_exceeded','quota_exhausted',
 'insufficient_quota','resource_exhausted','billing_hard_limit_reached',
 'credits_exhausted','usage_limit_reached','monthly_quota_exceeded','daily_quota_exceeded')
$Status=[ordered]@{ observed_utc=(Get-Date).ToUniversalTime().ToString('o')
    machine=$env:COMPUTERNAME; auth='UNKNOWN'; controller='UNKNOWN'; credential_import='NOT_ATTEMPTED'; bitrise_credential_import='NOT_ATTEMPTED'; appveyor='NOT_CONFIGURED'
    bitrise='NOT_CONFIGURED'; events_claimed=0; remote_cancellations_confirmed=0; remote_terminal_confirmed=0
    uncertain=0; fallback_dispatched=$false }
$mutex=New-Object System.Threading.Mutex($false,'Global\AntharesCiQuotaCancelStandby')
$owned=$false
function Property($o,[string]$name) {
    if($null -eq $o){return $null}
    if($o -is [System.Collections.IDictionary]){return $o[$name]}
    $p=$o.PSObject.Properties[$name]
    if($p){return $p.Value}
    return $null
}
function Secret([string]$name) {
    $path=Join-Path $SecretDir $name
    if(-not (Test-Path -LiteralPath $path -PathType Leaf)){return ''}
    $line=Get-Content -LiteralPath $path -Raw -ErrorAction Stop
    $sec=ConvertTo-SecureString -String $line.Trim() -ErrorAction Stop
    $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try{return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)}
    finally{[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)}
}
function CallProvider([string]$url,[string]$token,[string]$provider,
   [string]$method='GET',$body=$null) {
    $headers=@{Accept='application/json';'User-Agent'='AntharesRemote-QuotaStandby/1'}
    if($provider -eq 'appveyor'){$headers.Authorization='Bearer '+$token}
    else{$headers.Authorization=$token}
    $params=@{Uri=$url;Method=$method;Headers=$headers;TimeoutSec=12}
    if($null -ne $body){
        $params.Body=$body|ConvertTo-Json -Compress -Depth 7
        $params.ContentType='application/json'
    }
    Invoke-RestMethod @params
}
function QuotaCode($obj) {
    foreach($key in @('failure_reason','failure_code','error_code','code')){
        $v=Property $obj $key
        if($v -is [string] -and $QuotaCodes -contains $v.Trim().ToLowerInvariant()){
            return $v.Trim().ToLowerInvariant()
        }
    }
    foreach($entry in @(Property $obj 'messages')){
        $v=Property $entry 'code'
        if($v -is [string] -and $QuotaCodes -contains $v.Trim().ToLowerInvariant()){
            return $v.Trim().ToLowerInvariant()
        }
    }
    return $null
}
function Recent($obj){
    $v=Property $obj 'created'
    if(-not $v){$v=Property $obj 'triggered_at'}
    if(-not $v){$v=Property $obj 'created_at'}
    if(-not $v){return $false}
    try {
        $d=[DateTimeOffset]::Parse([string]$v)
        $seconds=([DateTimeOffset]::UtcNow-$d.ToUniversalTime()).TotalSeconds
        return $seconds -ge 0 -and $seconds -le 5400
    }catch{return $false}
}
function SignedLedger($body,[string]$key,[string]$Endpoint=$Controller) {
    $fields=@('phase','provider','target','sha','code','owner_token','outcome')
    $stamp=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds().ToString()
    $parts=@($stamp)
    foreach($f in $fields){
        $v=Property $body $f
        $parts+= if($null -eq $v){''}else{[string]$v}
    }
    $canonical=$parts -join "`n"
    $rsa=New-Object System.Security.Cryptography.RSACryptoServiceProvider
    try {
        $rsa.PersistKeyInCsp=$false
        $rsa.FromXmlString($key)
        $oid=[System.Security.Cryptography.CryptoConfig]::MapNameToOID('SHA256')
        $signature=[Convert]::ToBase64String($rsa.SignData(
            [Text.Encoding]::UTF8.GetBytes($canonical),$oid))
    }finally{$rsa.Dispose()}
    $headers=@{'X-Anthares-Device'='DESKTOP-FTDK0HP'
        'X-Anthares-Timestamp'=$stamp;'X-Anthares-Signature'=$signature}
    Invoke-RestMethod -Uri $Endpoint -Method Post -Headers $headers -TimeoutSec 18 `
      -ContentType 'application/json' -Body ($body|ConvertTo-Json -Compress -Depth 5)
}
function ImportSealedAppVeyor([string]$privateKey) {
    $file=Join-Path $SecretDir 'ci-quota-appveyor-token.dpapi'
    if(Test-Path -LiteralPath $file){return 'ALREADY_PROVISIONED'}
    $endpoint='https://anthares-ci-quota-controller.vercel.app/api/credential-bridge'
    try {
        $wrapped=SignedLedger @{phase='consume';provider='appveyor'} $privateKey $endpoint
    }catch{
        if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404){
            return 'NO_PENDING_TRANSFER'
        }
        return 'BRIDGE_UNAVAILABLE'
    }
    if((Property $wrapped 'code') -ne 'SEALED_CONSUMED'){return 'INVALID_TRANSFER_RECEIPT'}
    $bytes=$null
    $plain=$null
    $rsa=New-Object System.Security.Cryptography.RSACryptoServiceProvider
    try{
        $rsa.PersistKeyInCsp=$false
        $rsa.FromXmlString($privateKey)
        $sealed=[Convert]::FromBase64String([string](Property $wrapped 'sealed'))
        if($sealed.Length -ne 384){throw 'INVALID_ENVELOPE_LENGTH'}
        $bytes=$rsa.Decrypt($sealed,$true)
        $plain=[Text.Encoding]::UTF8.GetString($bytes)
        if($plain.Length -lt 12 -or $plain.Length -gt 340 -or
           $plain -match '[\r\n]'){throw 'INVALID_SECRET_SHAPE'}
        $doc=CallProvider 'https://ci.appveyor.com/api/projects/UniversoAnthares/anthares-kwai-runner' $plain 'appveyor'
        $project=Property $doc 'project'
        if((Property $project 'slug') -ne 'anthares-kwai-runner' -or
           (Property $project 'accountName') -ne 'UniversoAnthares' -or
           (Property $project 'repositoryName') -ne $Repo){throw 'SOURCE_NOT_OWNED'}
        $enc=($plain|ConvertTo-SecureString -AsPlainText -Force|ConvertFrom-SecureString)
        $enc|Set-Content -LiteralPath $file -Encoding ASCII
        & icacls.exe $file /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' |Out-Null
        if($LASTEXITCODE -ne 0){throw 'ACL_UNVERIFIED'}
        return 'IMPORT_VERIFIED_AND_DPAPI_PROTECTED'
    }catch{
        if(Test-Path $file){Remove-Item -LiteralPath $file -Force -ErrorAction SilentlyContinue}
        return 'IMPORT_FAILED_AFTER_CONSUME'
    }finally{
        if($null -ne $bytes){[Array]::Clear($bytes,0,$bytes.Length)}
        $plain=$null
        $rsa.Dispose()
    }
}
function ImportSealedBitrise([string]$privateKey,[string]$appSlug) {
    $file=Join-Path $SecretDir 'ci-quota-bitrise-token.dpapi'
    if(Test-Path -LiteralPath $file){return 'ALREADY_PROVISIONED'}
    if($appSlug -notmatch '^[a-f0-9-]{36}$'){return 'INVALID_APP_ID'}
    $endpoint='https://anthares-ci-quota-controller.vercel.app/api/credential-bridge'
    try {
        $wrapped=SignedLedger @{phase='consume';provider='bitrise'} $privateKey $endpoint
    }catch{
        if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 404){
            return 'NO_PENDING_TRANSFER'
        }
        return 'BRIDGE_UNAVAILABLE'
    }
    if((Property $wrapped 'code') -ne 'SEALED_CONSUMED' -or
       (Property $wrapped 'provider') -ne 'bitrise'){return 'INVALID_TRANSFER_RECEIPT'}
    $phase='INIT_RSA'
    $bytes=$null
    $plain=$null
    $rsa=New-Object System.Security.Cryptography.RSACryptoServiceProvider
    try{
        $phase='RSA_IMPORT'
        $rsa.PersistKeyInCsp=$false
        $rsa.FromXmlString($privateKey)
        $sealed=[Convert]::FromBase64String([string](Property $wrapped 'sealed'))
        if($sealed.Length -ne 384){throw 'INVALID_ENVELOPE_LENGTH'}
        $phase='RSA_OAEP_DECRYPT'
        $bytes=$rsa.Decrypt($sealed,$true)
        $phase='TOKEN_SHAPE'
        $plain=[Text.Encoding]::UTF8.GetString($bytes)
        if($plain.Length -lt 12 -or $plain.Length -gt 340 -or
           $plain -match '[\r\n]'){throw 'INVALID_SECRET_SHAPE'}
        $phase='API_AUTH_READ'
        $doc=CallProvider ('https://api.bitrise.io/v0.1/apps/'+[Uri]::EscapeDataString($appSlug)) $plain 'bitrise'
        $phase='PROJECT_IDENTITY'
        $app=Property $doc 'data'
        $repoUrl=[string](Property $app 'repo_url')
        if((Property $app 'slug') -ne $appSlug -or
           @('https://github.com/'+$Repo,
             'https://github.com/'+$Repo+'.git',
             'git@github.com:'+$Repo+'.git') -notcontains $repoUrl) {
            throw 'SOURCE_NOT_OWNED'
        }
        $phase='SYSTEM_DPAPI_ENCRYPT'
        $encrypted=($plain|ConvertTo-SecureString -AsPlainText -Force|ConvertFrom-SecureString)
        $encrypted|Set-Content -LiteralPath $file -Encoding ASCII
        $phase='ACL_RESTRICT'
        & icacls.exe $file /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' |Out-Null
        if($LASTEXITCODE -ne 0){throw 'ACL_UNVERIFIED'}
        return 'IMPORT_VERIFIED_AND_DPAPI_PROTECTED'
    }catch{
        if(Test-Path -LiteralPath $file){Remove-Item -LiteralPath $file -Force -ErrorAction SilentlyContinue}
        $status='IMPORT_FAILED_'+$phase
        if($phase -eq 'API_AUTH_READ' -and $_.Exception.Response){$status+='_' + [int]$_.Exception.Response.StatusCode}
        return $status
    }finally{
        if($null -ne $bytes){[Array]::Clear($bytes,0,$bytes.Length)}
        $plain=$null
        $rsa.Dispose()
    }
}
function Terminal($e,$obj) {
    if($e.provider -eq 'appveyor'){
        $b=Property $obj 'build'
        if((Property $b 'version') -ne $e.version -or
           (Property $b 'commitId') -ne $e.sha -or
           (Property $b 'branch') -ne 'main'){return $false}
        return @('failed','canceled','cancelled') -contains
             ([string](Property $b 'status')).ToLowerInvariant()
    }
    $b=Property $obj 'data'
    if((Property $b 'slug') -ne $e.slug -or
       (Property $b 'commit_hash') -ne $e.sha -or
       (Property $b 'branch') -ne 'main'){return $false}
    return @('2','3','4') -contains [string](Property $b 'status')
}
function ProcessEvent($e,[string]$key) {
    $message=@{phase='claim';provider=$e.provider;target=$e.target;sha=$e.sha;code=$e.code}
    try{$claim=SignedLedger $message $key}
    catch{
        if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 409) {
            return 'DEDUPED'
        }
        return 'CONTROLLER_CLAIM_UNAVAILABLE'
    }
    if((Property $claim 'code') -ne 'CLAIMED'){return 'CLAIM_NOT_CONFIRMED'}
    $Status.events_claimed++
    $result='CANCEL_UNCONFIRMED'
    $cancelWasRequested=$false
    try {
        $before=CallProvider $e.lookup $e.token $e.provider
        if(Terminal $e $before){$result='CANCELLED_NO_INDEPENDENT_RESERVE'}
        else {
            if($e.provider -eq 'appveyor') {
                $b=Property $before 'build'
                if((Property $b 'commitId') -ne $e.sha -or
                   (Property $b 'version') -ne $e.version -or
                   (Property $b 'branch') -ne 'main' -or
                   @('queued','running','starting') -notcontains
                    ([string](Property $b 'status')).ToLowerInvariant()){
                    throw 'UNSAFE_REMOTE_IDENTITY'
                }
                $cancelWasRequested=$true
                $null=CallProvider $e.cancel $e.token $e.provider 'DELETE'
            } else {
                $b=Property $before 'data'
                if((Property $b 'commit_hash') -ne $e.sha -or
                   (Property $b 'slug') -ne $e.slug -or
                   (Property $b 'branch') -ne 'main' -or
                   [string](Property $b 'status') -ne '0'){
                    throw 'UNSAFE_REMOTE_IDENTITY'
                }
                $cancelWasRequested=$true
                $null=CallProvider $e.cancel $e.token $e.provider 'POST' @{
                    abort_reason='Confirmed provider quota exhaustion';abort_with_success=$false
                }
            }
            foreach($i in 1..3){
                $after=CallProvider $e.lookup $e.token $e.provider
                if(Terminal $e $after){
                    $result='CANCELLED_NO_INDEPENDENT_RESERVE';break
                }
                Start-Sleep -Seconds 2
            }
        }
    }catch{
        # HTTP refusal, timeout or unknown terminal state: never retry cancellation.
    }
    try {
        $report=@{phase='report';provider=$e.provider;target=$e.target
           sha=$e.sha;code=$e.code;owner_token=$claim.owner_token;outcome=$result}
        $ack=SignedLedger $report $key
        if((Property $ack 'code') -ne 'RECORDED'){return 'REPORT_UNCONFIRMED'}
    }catch{return 'REPORT_UNCONFIRMED'}
    if($result -eq 'CANCELLED_NO_INDEPENDENT_RESERVE'){
        $Status.remote_terminal_confirmed++
        if($cancelWasRequested){$Status.remote_cancellations_confirmed++}
    }else{$Status.uncertain++}
    return $result
}
function AppVeyor($config,[string]$token,[string]$key) {
    $acc=[string](Property $config 'appveyor_account')
    $proj=[string](Property $config 'appveyor_project')
    if(-not $token -or $acc -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$' -or
       $proj -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$'){return 'NOT_CONFIGURED'}
    $base="https://ci.appveyor.com/api/projects/$([Uri]::EscapeDataString($acc))/$([Uri]::EscapeDataString($proj))"
    $history=CallProvider ($base+'/history?recordsNumber=12&branch=main') $token 'appveyor'
    if((Property (Property $history 'project') 'repositoryName') -ne $Repo){return 'PROJECT_MISMATCH'}
    $count=0
    foreach($item in @($history.builds)|Select-Object -First 12){
        if((Property $item 'branch') -ne 'main' -or -not (Recent $item)){continue}
        $v=[string](Property $item 'version')
        if($v -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$'){continue}
        $lookup=$base+'/build/'+[Uri]::EscapeDataString($v)
        $detail=CallProvider $lookup $token 'appveyor'
        $b=Property $detail 'build'
        if((Property (Property $detail 'project') 'repositoryName') -ne $Repo -or
           (Property $b 'branch') -ne 'main' -or (Property $b 'version') -ne $v){continue}
        $sha=[string](Property $b 'commitId');$reason=QuotaCode $b
        if($sha -match '^[a-f0-9]{40}$' -and $reason){
            $e=@{provider='appveyor';target=$acc+'__'+$proj+'__'+$v
                sha=$sha;code=$reason;version=$v;token=$token;lookup=$lookup
                cancel="https://ci.appveyor.com/api/builds/$([Uri]::EscapeDataString($acc))/$([Uri]::EscapeDataString($proj))/$([Uri]::EscapeDataString($v))"}
            $r=ProcessEvent $e $key;$count++
            if($r -match 'UNAVAILABLE|UNCONFIRMED'){return $r}
        }
    }
    return "READY_EVENTS_$count"
}
function Bitrise($config,[string]$token,[string]$key) {
    $app=[string](Property $config 'bitrise_app_slug')
    if(-not $token -or $app -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$'){
        return 'NOT_CONFIGURED'
    }
    $base='https://api.bitrise.io/v0.1/apps/'+[Uri]::EscapeDataString($app)
    $meta=CallProvider $base $token 'bitrise'
    $repoUrl=[string](Property (Property $meta 'data') 'repo_url')
    if(@('https://github.com/'+$Repo,'https://github.com/'+$Repo+'.git',
       'git@github.com:'+$Repo+'.git') -notcontains $repoUrl){return 'PROJECT_MISMATCH'}
    $history=CallProvider ($base+'/builds?limit=12&branch=main') $token 'bitrise'
    $count=0
    foreach($item in @((Property $history 'data'))|Select-Object -First 12){
        if((Property $item 'branch') -ne 'main' -or -not (Recent $item)){continue}
        $slug=[string](Property $item 'slug')
        if($slug -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{1,119}$'){continue}
        $lookup=$base+'/builds/'+[Uri]::EscapeDataString($slug)
        $detail=CallProvider $lookup $token 'bitrise';$b=Property $detail 'data'
        if((Property $b 'slug') -ne $slug -or (Property $b 'branch') -ne 'main'){continue}
        $sha=[string](Property $b 'commit_hash');$reason=QuotaCode $b
        if($sha -match '^[a-f0-9]{40}$' -and $reason){
            $e=@{provider='bitrise';target=$app+'__'+$slug;sha=$sha;code=$reason
                slug=$slug;token=$token;lookup=$lookup;cancel=$lookup+'/abort'}
            $r=ProcessEvent $e $key;$count++
            if($r -match 'UNAVAILABLE|UNCONFIRMED'){return $r}
        }
    }
    return "READY_EVENTS_$count"
}
try {
    $owned=$mutex.WaitOne(0)
    if(-not $owned){$Status.auth='ALREADY_RUNNING';return}
    if($env:COMPUTERNAME -ne 'DESKTOP-FTDK0HP' -or
       [Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne 'S-1-5-18'){
        $Status.auth='WRONG_WINDOWS_IDENTITY';return
    }
    $configFile=Join-Path $StateDir 'ci-quota-standby.json'
    if(-not (Test-Path -LiteralPath $configFile)){$Status.auth='CONFIG_MISSING';return}
    $config=Get-Content -LiteralPath $configFile -Raw|ConvertFrom-Json
    $privateKey=Secret 'ci-quota-remote-rsa.dpapi'
    if($privateKey.Length -lt 200){$Status.auth='AUTH_NOT_CONFIGURED';return}
    $Status.auth='READY_DPAPI_SYSTEM'
    try {
        $probe=SignedLedger @{phase='health'} $privateKey
        if((Property $probe 'code') -ne 'REMOTE_AUTH_READY'){throw 'CONTROLLER_NOT_READY'}
        $Status.controller='READY_RSA_NEON'
    }catch{
        $Status.controller='AUTH_OR_LEDGER_UNAVAILABLE'
        return
    }
    $Status.credential_import=ImportSealedAppVeyor $privateKey
    try{$Status.appveyor=AppVeyor $config (Secret 'ci-quota-appveyor-token.dpapi') $privateKey}
    catch{$Status.appveyor='SOURCE_UNAVAILABLE'}
    $Status.bitrise_credential_import=ImportSealedBitrise $privateKey ([string]$config.bitrise_app_slug)
    try{$Status.bitrise=Bitrise $config (Secret 'ci-quota-bitrise-token.dpapi') $privateKey}
    catch{$Status.bitrise='SOURCE_UNAVAILABLE'}
}finally{
    if(-not (Test-Path -LiteralPath $StateDir)){New-Item -ItemType Directory -Path $StateDir -Force|Out-Null}
    $Status.observed_utc=(Get-Date).ToUniversalTime().ToString('o')
    $Status|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $StateDir 'ci-quota-standby-status.json') -Encoding UTF8
    if($owned){$mutex.ReleaseMutex()}
    $mutex.Dispose()
}
$Status|ConvertTo-Json -Compress
