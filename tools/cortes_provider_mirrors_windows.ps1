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
    $entry|ConvertTo-Json -Compress|Set-Content -Encoding UTF8 -Path $Report
    Write-Output ($entry|ConvertTo-Json -Compress)
}
function Git([string[]]$args) {
    $output=(& git -C $Checkout @args 2>&1|Out-String).Trim()
    if($LASTEXITCODE -ne 0){throw 'GIT_STEP_FAILED'}
    return $output
}
function Descendant([string]$ancestor,[string]$descendant) {
    & git -C $Checkout merge-base --is-ancestor $ancestor $descendant 2>$null
    return $LASTEXITCODE -eq 0
}
try {
    if(-not (Test-Path (Join-Path $Checkout '.git'))) {
        $parent=Split-Path -Parent $Checkout
        New-Item -ItemType Directory -Force $parent|Out-Null
        & git clone -q --no-checkout 'https://github.com/UniversoAnthares/anthares-kwai-runner.git' $Checkout
        if($LASTEXITCODE -ne 0){throw 'INITIAL_CLONE_FAILED'}
    }
    $existing=@(Git @('remote'))
    foreach($provider in @('gitlab','codeberg')) {
        $url=if($provider -eq 'gitlab') {'https://gitlab.com/UniversoAnthares/anthares-kwai-runner.git'} else {'https://codeberg.org/UniversoAnthares/anthares-kwai-runner.git'}
        if(-not ((Git @('remote')) -split '\r?\n' -contains $provider)){
            Git @('remote','add',$provider,$url)|Out-Null
        }
    }
    # Never switch authority to an unverified stale provider after an outage.
    Git @('fetch','--no-tags','origin','+refs/heads/main:refs/remotes/origin/main')|Out-Null
    $source=Git @('rev-parse','refs/remotes/origin/main')
    if($source -notmatch '^[a-f0-9]{40}$'){throw 'GITHUB_SHA_INVALID'}
    foreach($provider in @('gitlab','codeberg')) {
        try{
            Git @('fetch','--no-tags',$provider,('+refs/heads/main:refs/remotes/'+$provider+'/main'))|Out-Null
            $target=Git @('rev-parse',('refs/remotes/'+$provider+'/main'))
            if($target -eq $source){Audit $provider 'PROVEN' $source;continue}
            if(Descendant $target $source){
                # A fast-forward cannot erase or rewrite the provider's history.
                Git @('push',$provider,'refs/remotes/origin/main:refs/heads/main')|Out-Null
            }elseif(Descendant $source $target){
                # Provider is ahead: leave the provider intact.
                Audit $provider 'AHEAD_OR_RECONCILIATION_PENDING' 'NO_FORCE_PUSH';continue
            }elseif($provider -eq 'gitlab'){
                # GitLab mirror may contain safe sync merge commits. Merge in a
                # disposable workspace; abort on any conflict, never force.
                Git @('checkout','-f','-B','anthares-gitlab-mirror-sync','refs/remotes/origin/main')|Out-Null
                $merge=(& git -C $Checkout -c user.name='Anthares Git Mirror' -c user.email='sync@anthares.invalid' merge --no-edit --no-ff 'refs/remotes/gitlab/main' -m 'sync: reconcile GitLab mirror with GitHub main' 2>&1|Out-String)
                if($LASTEXITCODE -ne 0) {
                    & git -C $Checkout merge --abort 2>$null|Out-Null
                    throw 'GITLAB_MERGE_CONFLICT'
                }
                Git @('push','gitlab','HEAD:refs/heads/main')|Out-Null
            }else{throw 'CODEBERG_DIVERGED_NO_FORCE_PUSH'}
            # An acknowledged push is not sufficient without SHA readback.
            $remote=(& git -C $Checkout ls-remote $provider refs/heads/main 2>$null|Out-String).Trim()
            if($LASTEXITCODE -ne 0){throw 'READBACK_FAILED'}
            $actual=($remote -split '\s+')[0]
            $expected=if($provider -eq 'gitlab' -and ((Git @('branch','--show-current')) -eq 'anthares-gitlab-mirror-sync')) {(Git @('rev-parse','HEAD'))}else{$source}
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
