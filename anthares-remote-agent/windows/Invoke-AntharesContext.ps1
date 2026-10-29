[CmdletBinding()]
param(
 [ValidateSet('Invoke','Serve','Stop')][string]$Mode='Invoke',
 [ValidateSet('Windows','Cloudflare','GitHub','Hostinger')][string]$Service='Windows',
 [string]$ArgumentsJson='["identity"]',
 [string]$WorkingDirectory='',
 [ValidateRange(5,120)][int]$TimeoutSeconds=45,
 [string]$RequestId=([guid]::NewGuid().ToString('N'))
)
$ErrorActionPreference='Stop'
if($Mode -eq 'Serve'){throw 'Use the registered Anthares Context Router User task; Python owns the server lifecycle'}
$cfg=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'config.json') -Raw|ConvertFrom-Json
$argsList=ConvertFrom-Json -InputObject $ArgumentsJson
if($Mode -eq 'Stop'){$Service='Lifecycle';$argsList=@('stop')}
$req=@{id=$RequestId;service=$Service;arguments=@($argsList);cwd=$WorkingDirectory;timeout=$TimeoutSeconds}
$encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(($req|ConvertTo-Json -Compress -Depth 6)))
$psi=New-Object Diagnostics.ProcessStartInfo
$psi.FileName=$cfg.python
$psi.Arguments='-B "'+(Join-Path $PSScriptRoot 'context_router.py')+'" --request-b64 '+$encoded
$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true
$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
$p=New-Object Diagnostics.Process;$p.StartInfo=$psi
try{
 [void]$p.Start()
 $line=$p.StandardOutput.ReadLineAsync()
 if(-not $line.Wait(($TimeoutSeconds+25)*1000)){throw 'RESULT_UNCERTAIN: reconcile request ID before resending'}
 if(-not $line.Result){throw 'BROKER_CLIENT_FAILED: no framed result'}
 $line.Result
}finally{$p.Dispose()}
