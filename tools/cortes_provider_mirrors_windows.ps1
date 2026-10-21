# Independent Windows Git mirror; NO GitHub Actions or GitLab CI minutes.
# Uses the interactive Windows account's existing OS Git credentials.
# No PAT values, passwords or credential URLs may be stored or logged.
param(
    [string]$Checkout = 'D:\AntharsWork\cortes-provider-mirror',
    [string]$Report = 'D:\AntharsWork\cortes-provider-mirror\mirror-health.json'
)
$ErrorActionPreference = 'Stop'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'Never'
$mutex = New-Object System.Threading.Mutex($false, 'Local\AntharesCortesGitMirror')
if (-not $mutex.WaitOne(0)) { exit 0 }
function Audit([string]$provider,[string]$state,[string]$detail) {
    $entry = @{at=(Get-Date).ToUniversalTime().ToString('o');provider=$provider;state=$state;detail=$detail}
    $dir=Split-Path -Parent $Report
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir|Out-Null }
    $encoded=$entry|ConvertTo-Json -Compress
    $safeProvider=$provider -replace '[^a-zA-Z0-9_-]','_'
    $folder=Split-Path -Parent $Report
    $filename=Join-Path $folder ('mirror-health-'+$safeProvider+'.json')
    $encoded|Set-Content -Encoding UTF8 -Path $filename
    $encoded|Add-Content -Encoding UTF8 -Path (Join-Path $folder 'mirror-events.jsonl')
    Write-Output $encoded
}
function Invoke-ProviderGit([string[]]$args) {
    $output=(& git.exe -C $Checkout @args 2>&1|Out-String).Trim()
    if($LASTEXITCODE -ne 0){throw 'GIT_STEP_FAILED'}
    return $output
}
function Descendant([string]$ancestor,[string]$descendant) {
    & git.exe -C $Checkout merge-base --is-ancestor $ancestor $descendant 2>$null
    return $LASTEXITCODE -eq 0
}
try {
    if(-not (Test-Path (Join-Path $Checkout '.git'))) {
        $parent=Split-Path -Parent $Checkout
        New-Item -ItemType Directory -Force $parent|Out-Null
        & git.exe clone -q --no-checkout 'https://github.com/UniversoAnthares/anthares-kwai-runner.git' $Checkout
        if($LASTEXITCODE -ne 0){throw 'INITIAL_CLONE_FAILED'}
    }
    $existing=@(Invoke-ProviderGit @('remote'))
    foreach($provider in @('gitlab','codeberg')) {
        $url=if($provider -eq 'gitlab') {'https://gitlab.com/UniversoAnthares/anthares-kwai-runner.git'} else {'https://codeberg.org/UniversoAnthares/anthares-kwai-runner.git'}
        if(-not ((Invoke-ProviderGit @('remote')) -split '\r?\n' -contains $provider)){
            Invoke-ProviderGit @('remote','add',$provider,$url)|Out-Null
        }
    }
    # Never switch authority to an unverified stale provider after an outage.
    Invoke-ProviderGit @('fetch','--no-tags','origin','+refs/heads/main:refs/remotes/origin/main')|Out-Null
    $source=Invoke-ProviderGit @('rev-parse','refs/remotes/origin/main')
    if($source -notmatch '^[a-f0-9]{40}$'){throw 'GITHUB_SHA_INVALID'}
    foreach($provider in @('gitlab','codeberg')) {
        try{
            Invoke-ProviderGit @('fetch','--no-tags',$provider,('+refs/heads/main:refs/remotes/'+$provider+'/main'))|Out-Null
            $target=Invoke-ProviderGit @('rev-parse',('refs/remotes/'+$provider+'/main'))
            if($target -eq $source){Audit $provider 'PROVEN' $source;continue}
            if(Descendant $target $source){
                # A fast-forward cannot erase or rewrite the provider's history.
                Invoke-ProviderGit @('push',$provider,'refs/remotes/origin/main:refs/heads/main')|Out-Null
            }elseif(Descendant $source $target){
                # Provider is ahead: leave the provider intact.
                Audit $provider 'AHEAD_OR_RECONCILIATION_PENDING' 'NO_FORCE_PUSH';continue
            }elseif($provider -eq 'gitlab'){
                # GitLab mirror may contain safe sync merge commits. Merge in a
                # disposable workspace; abort on any conflict, never force.
                Invoke-ProviderGit @('checkout','-f','-B','anthares-gitlab-mirror-sync','refs/remotes/origin/main')|Out-Null
                $merge=(& git.exe -C $Checkout -c user.name='Anthares Git Mirror' -c user.email='sync@anthares.invalid' merge --no-edit --no-ff 'refs/remotes/gitlab/main' -m 'sync: reconcile GitLab mirror with GitHub main' 2>&1|Out-String)
                if($LASTEXITCODE -ne 0) {
                    & git.exe -C $Checkout merge --abort 2>$null|Out-Null
                    throw 'GITLAB_MERGE_CONFLICT'
                }
                Invoke-ProviderGit @('push','gitlab','HEAD:refs/heads/main')|Out-Null
            }else{throw 'CODEBERG_DIVERGED_NO_FORCE_PUSH'}
            # An acknowledged push is not sufficient without SHA readback.
            $remote=(& git.exe -C $Checkout ls-remote $provider refs/heads/main 2>$null|Out-String).Trim()
            if($LASTEXITCODE -ne 0){throw 'READBACK_FAILED'}
            $actual=($remote -split '\s+')[0]
            $expected=if($provider -eq 'gitlab' -and ((Invoke-ProviderGit @('branch','--show-current')) -eq 'anthares-gitlab-mirror-sync')) {(Invoke-ProviderGit @('rev-parse','HEAD'))}else{$source}
            if($actual -ne $expected){throw 'REMOTE_SHA_MISMATCH'}
            Audit $provider 'PROVEN' $actual
        }catch{
            $reason=if($provider -eq 'codeberg'){'CODEBERG_AUTH_OR_DIVERGENCE_REQUIRES_REVIEW'}else{'GITLAB_SYNC_REQUIRES_REVIEW'}
            Audit $provider 'BLOCKED' $reason
        }
    }
}catch{
    Audit 'all' 'BLOCKED' 'SOURCE_OR_LOCAL_WORKTREE_UNAVAILABLE'
}finally{
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
