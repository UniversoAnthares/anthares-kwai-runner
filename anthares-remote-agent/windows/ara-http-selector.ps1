# ARA HTTP transport selector; no duplicate executor.
# Reuse the existing shared-Neon Cloudflare standby whenever it accepts the
# authenticated device. Never select an unverified endpoint.
function Test-AraHttpTransport {
  param([string]$Origin,[string]$Token,[string]$Device='DESKTOP-FTDK0HP',[int]$Timeout=6)
  if($Origin -notmatch '^https://[a-z0-9.-]+$' -or [string]::IsNullOrWhiteSpace($Token)){return $false}
  try {
    $headers=@{Authorization=('Bearer '+$Token);'X-Anthares-Device'=$Device}
    $r=Invoke-RestMethod -Method Get -Uri ($Origin+'/v1/device/auth-check') -Headers $headers -TimeoutSec $Timeout -ErrorAction Stop
    return [bool]($r.ok -eq $true -and $r.backend -eq 'vercel-neon')
  }catch{return $false}
}
function Select-AraHttpTransport {
  param([string]$Primary='https://anthares-ara-neon-standby.anthares1.workers.dev',
        [string]$Secondary='https://anthares-remote-primary.vercel.app',
        [string]$Tertiary='https://anthares-remote-secondary.vercel.app',
        [string]$Token=$env:ANTHARES_DEVICE_TOKEN,
        [string]$Device='DESKTOP-FTDK0HP',
        [switch]$SimulatePrimaryFailure)
  $primaryOk=$false
  if(-not $SimulatePrimaryFailure){$primaryOk=Test-AraHttpTransport -Origin $Primary -Token $Token -Device $Device}
  $secondaryOk=$false
  if(-not $primaryOk){$secondaryOk=Test-AraHttpTransport -Origin $Secondary -Token $Token -Device $Device}
  $tertiaryOk=$false
  if(-not $primaryOk -and -not $secondaryOk){$tertiaryOk=Test-AraHttpTransport -Origin $Tertiary -Token $Token -Device $Device}
  # No HTTP origin is safer than launching a permanent HTTP-402 poll loop.
  # Private GitHub/GitLab issue queues remain active in the same C8 process.
  $origin=if($primaryOk){$Primary}elseif($secondaryOk){$Secondary}elseif($tertiaryOk){$Tertiary}else{$null}
  $reason=if($primaryOk){'shared_neon_standby_verified'}elseif($secondaryOk){'legacy_vercel_primary_verified'}elseif($tertiaryOk){'legacy_vercel_secondary_verified'}else{'all_http_unavailable_queue_only'}
  [pscustomobject]@{origin=$origin;reason=$reason;primary_ok=$primaryOk;secondary_ok=$secondaryOk;tertiary_ok=$tertiaryOk}
}
