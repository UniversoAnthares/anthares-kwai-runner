# ARA HTTP transport selector; no duplicate executor.
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
  param([string]$Primary='https://anthares-remote-primary.vercel.app',
        [string]$Secondary='https://anthares-remote-secondary.vercel.app',
        [string]$Token=$env:ANTHARES_DEVICE_TOKEN,
        [string]$Device='DESKTOP-FTDK0HP',
        [switch]$SimulatePrimaryFailure)
  $primaryOk=$false
  if(-not $SimulatePrimaryFailure){$primaryOk=Test-AraHttpTransport -Origin $Primary -Token $Token -Device $Device}
  $secondaryOk=$false
  if(-not $primaryOk){$secondaryOk=Test-AraHttpTransport -Origin $Secondary -Token $Token -Device $Device}
  # A disabled Vercel deployment (402) must not start a failing HTTP loop.
  # A blank origin allows the same C8 process to use its configured private queues.
  $origin=if($primaryOk){$Primary}elseif($secondaryOk){$Secondary}else{$null}
  $reason=if($primaryOk){'primary_verified'}elseif($secondaryOk){'secondary_verified'}else{'both_unavailable_queue_only'}
  [pscustomobject]@{origin=$origin;reason=$reason;primary_ok=$primaryOk;secondary_ok=$secondaryOk}
}
