Set-StrictMode -Version Latest
function Get-SSHRecoveryDecision {
  param([int]$PrimaryCount,[int]$ReserveCount,[bool]$RecoveryOwnerActive,
    [bool]$TasksValid,[datetimeoffset]$Now,[object]$State)
  $since=$Now; $lastAction=$null
  if($State){
    $last=[datetimeoffset]::Parse($State.last_observed_utc)
    if($last -gt $Now){throw 'future observation'}
    if(($Now-$last).TotalSeconds -le 35 -and $State.missing_since_utc){$since=[datetimeoffset]::Parse($State.missing_since_utc)}
    if($State.last_action_utc){$lastAction=[datetimeoffset]::Parse($State.last_action_utc)}
  }
  if($since -gt $Now){throw 'future absence timestamp'}
  $reason='observing';$action='None'
  if(-not $TasksValid){$reason='invalid-canonical-tasks';$since=$Now}
  elseif($PrimaryCount -gt 0 -or $ReserveCount -gt 0){$reason='existing-executor';$since=$Now}
  elseif($RecoveryOwnerActive){$reason='canonical-recovery-owner-active';$since=$Now}
  elseif(($Now-$since).TotalSeconds -lt 90){$reason='grace-period'}
  elseif($lastAction -and ($Now-$lastAction).TotalSeconds -lt 120){$reason='cooldown'}
  else{$action='StartCanonicalRecovery';$reason='recovery-owner-absent-after-grace'}
  [pscustomobject]@{action=$action;reason=$reason;missing_since_utc=$since.ToString('o');last_observed_utc=$Now.ToString('o');last_action_utc=if($lastAction){$lastAction.ToString('o')}else{$null}}
}
Export-ModuleMember -Function Get-SSHRecoveryDecision
