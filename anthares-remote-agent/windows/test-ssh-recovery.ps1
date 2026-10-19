$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'ssh-recovery-policy.psm1') -Force
$t=[datetimeoffset]::Parse('2026-10-19T00:00:00Z')
function Decide($seconds,$state=$null,$p=0,$r=0,$w=$false,$valid=$true){Get-SSHRecoveryDecision -PrimaryCount $p -ReserveCount $r -RecoveryOwnerActive $w -TasksValid $valid -Now ($t.AddSeconds($seconds)) -State $state}
function Assert($condition,$message){if(-not $condition){throw $message}}
$s=Decide 0;Assert ($s.action -eq 'None') 'must observe first'
foreach($second in @(15,30,45,60,75,89)){$s=Decide $second $s;Assert ($s.action -eq 'None') '90 second grace violated'}
$ready=Decide 90 $s;Assert ($ready.action -eq 'StartCanonicalRecovery') 'eligible recovery missing'
Assert ((Decide 90 $s 1).action -eq 'None') 'primary authority violated'
Assert ((Decide 90 $s 0 1).action -eq 'None') 'reserve authority violated'
Assert ((Decide 90 $s 0 0 $true).action -eq 'None') 'watchdog authority violated'
Assert ((Decide 90 $s 0 0 $false $false).action -eq 'None') 'invalid task accepted'
Assert ((Decide 150 $s).action -eq 'None') 'stale evidence accepted'
$ready.last_action_utc=$t.AddSeconds(85).ToString('o')
Assert ((Decide 100 $ready).reason -eq 'cooldown') 'duplicate recovery accepted'
$future=Decide 120;$rejected=$false
try{Decide 90 $future|Out-Null}catch{$rejected=$true}
Assert $rejected 'future state accepted'
$entry=Get-Content (Join-Path $PSScriptRoot 'ssh-recovery.ps1') -Raw
Assert ($entry -notmatch '(?i)\b(Stop-Process|Stop-ScheduledTask|Restart-Computer|Restart-Service|Invoke-Expression)\b') 'entry has destructive or arbitrary execution'
Write-Output 'SSH_RECOVERY_POLICY_PROVEN=1 grace=90 stale=reject cooldown=120 single_authority=canonical-recovery-task'
