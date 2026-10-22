$ErrorActionPreference='Stop'
$root='D:\AntharsWork\cortes-social-browser-20261020'
$folder=Join-Path $root 'qa-incidents'
$base='D:\AntharsWork\AntharesRemote'
$state=Join-Path $base 'cortes-p0-delivered.json'
$log=Join-Path $base 'cortes-p0-delivery.log'
$mutex=New-Object Threading.Mutex($false,'Global\AntharesCortesP0Delivery')
$held=$false
function Note([string]$v){Add-Content $log ((Get-Date -Format o)+' '+$v)}
try{
 $held=$mutex.WaitOne(500)
 if(!$held -or !(Test-Path $folder)){exit 0}
 $seen=@{}
 if(Test-Path $state){try{$old=Get-Content $state -Raw|ConvertFrom-Json;foreach($x in $old.PSObject.Properties){$seen[$x.Name]=$x.Value}}catch{}}
 $incidents=@(); $pending=@{}
 $recent=Get-ChildItem $folder -File -Filter '*.json'|Where-Object {$_.LastWriteTime -gt (Get-Date).AddHours(-24)}|Sort-Object LastWriteTime
 foreach($file in $recent){
  try{$e=Get-Content $file.FullName -Raw -Encoding UTF8|ConvertFrom-Json}catch{continue}
  if($e.priority -ne 'P0' -or [string]::IsNullOrWhiteSpace([string]$e.network)){continue}
  $finger=if($e.fingerprint){[string]$e.fingerprint}else{[string]$e.kind}
  $key=(Get-Date -Format 'yyyy-MM-dd')+':'+$e.network+':'+$e.kind+':'+$finger
  if(!$seen.ContainsKey($key)){$incidents+=@{key=$key;name=$file.Name;network=$e.network;kind=$e.kind}}
 }
 if($incidents.Count -eq 0){exit 0}
 . 'C:\ProgramData\AntharesRemoteAgent\load-issue-queue-auth.ps1'
 $auth=[string]$env:ANTHARES_GITHUB_QUEUE_TOKEN
 if(!$auth){Note 'AUTH_MISSING';exit 2}
 $head=@{Authorization='Bearer '+$auth;Accept='application/vnd.github+json';'User-Agent'='Anthares-CORTES-P0';'X-GitHub-Api-Version'='2022-11-28'}
 $url='https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/issues/283/comments'
 foreach($row in @($incidents | Select-Object -First 8)){
   $desc='[QA P0][AUTO] Failure: '+$row.kind+'; network='+$row.network+'; evidence='+$row.name+'; fingerprint='+$row.key+'. Investigate immediately. Preserve uncertain posts; no blind retry.'
   $payload=@{body=$desc}|ConvertTo-Json -Compress
   try{
    $resp=Invoke-RestMethod $url -Headers $head -Method POST -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -ContentType 'application/json; charset=utf-8' -TimeoutSec 24
    if(!$resp.id){throw 'COMMENT_CONFIRMATION_MISSING'}
    $seen[$row.key]=[datetimeoffset]::Now.ToString('o')
    $tmp=$state+'.tmp'
    $seen|ConvertTo-Json -Depth 3|Set-Content $tmp -Encoding UTF8
    Move-Item $tmp $state -Force
    Note ('P0_GITHUB_DELIVERED='+$row.network+' comment_id='+$resp.id)
   }catch{Note ('P0_GITHUB_FAILED='+$row.network+' type='+$_.Exception.GetType().Name)}
 }
}finally{
 Remove-Item Env:\ANTHARES_GITHUB_QUEUE_TOKEN -ErrorAction SilentlyContinue
 if($held){$mutex.ReleaseMutex()}
 $mutex.Dispose()
}

