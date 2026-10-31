# ARA HTTP selector: one shared-Neon Cloudflare origin, independent private queues.
function Test-AraHttpTransport {
  param([string]$Origin,[string]$Token,[string]$Device='DESKTOP-FTDK0HP',[int]$Timeout=6)
  if($Origin -notmatch '^https://[a-z0-9.-]+$' -or [string]::IsNullOrWhiteSpace($Token)){return $false}
  try {
    $headers=@{Authorization=('Bearer '+$Token);'X-Anthares-Device'=$Device}
    $r=Invoke-RestMethod -Method Get -Uri ($Origin+'/v1/device/auth-check') -Headers $headers -TimeoutSec $Timeout -ErrorAction Stop
    # Preserve the currently deployed shared-Neon API response contract.
    return [bool]($r.ok -eq $true -and $r.backend -eq 'vercel-neon')
  }catch{return $false}
}
function Select-AraHttpTransport {
  param([string]$Primary='https://anthares-ara-neon-standby.anthares1.workers.dev',
        [string]$Token=$env:ANTHARES_DEVICE_TOKEN,
        [string]$Device='DESKTOP-FTDK0HP',
        [switch]$SimulatePrimaryFailure)
  $primaryOk=$false
  if(-not $SimulatePrimaryFailure){$primaryOk=Test-AraHttpTransport -Origin $Primary -Token $Token -Device $Device}
  # On failure, leave HTTP disabled and retain the single C8 agent's GitHub/GitLab issue queues.
  $origin=if($primaryOk){$Primary}else{$null}
  $reason=if($primaryOk){'shared_neon_standby_verified'}else{'http_unavailable_private_queues'}
  [pscustomobject]@{origin=$origin;reason=$reason;primary_ok=$primaryOk;secondary_ok=$false;tertiary_ok=$false}
}
