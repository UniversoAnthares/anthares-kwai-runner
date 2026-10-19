// A fixed, reviewed MCP regression suite. No caller-supplied commands or code.
export const approvedTestTool = {
 name:'run_tests',scope:'github.write',
 description:'Run the approved Anthares MCP regression suite through Anthares Remote. Tests the exact deployed reviewed source, not arbitrary branch code. Returns source SHA and pass/fail counts.',
 inputSchema:{type:'object',additionalProperties:false,properties:{suite:{type:'string',enum:['mcp-regression']},request_id:{type:'string',description:'Unique UUID for this requested run; replay is rejected.'}},required:['suite','request_id']}
};
export function approvedTestCommand(source) {
 if(!/^[a-f0-9]{40}$/.test(String(source||'')))throw Error('test_source_unconfigured');
 const root='C:\\Users\\Lucas\\.codex\\visualizations\\2026\\10\\18\\01a14ef0-a2b5-73c0-9c47-d8d5ee50c5e0\\ara-recovery';
 return `$ErrorActionPreference='Stop'
$mutex=New-Object Threading.Mutex($false,'Global\\AntharesMcpApprovedRegression')
if(-not $mutex.WaitOne(0)){throw 'test_suite_busy'}
try{
 $r='${root}'
 $source='${source}'
 $work=Join-Path ([IO.Path]::GetTempPath()) ('AntharesMcpQA-'+[guid]::NewGuid().ToString('N'))
 [void][IO.Directory]::CreateDirectory($work)
 $archive=Join-Path $work 'source.zip'
 git -c safe.directory=$r -C $r archive --format=zip --output=$archive $source cloudflare-ara-mcp
 if($LASTEXITCODE -ne 0){throw 'approved_source_unavailable'}
 Expand-Archive -LiteralPath $archive -DestinationPath $work
 Set-Location (Join-Path $work 'cloudflare-ara-mcp')
 $env:MINIFLARE_MODULE='file:///C:/Users/Lucas/AppData/Local/npm-cache/_npx/31df52248099582d/node_modules/miniflare/dist/src/index.js'
 $lines=@(node --test --test-reporter=tap src/claude-client-policy.test.mjs src/github-bridge.test.mjs src/owner-github-auth.test.mjs src/approved-tests.test.mjs worker-runtime.test.mjs 2>&1)
 $testExit=$LASTEXITCODE
 $report=$lines -join [Environment]::NewLine
 $passed=[regex]::Match($report,'(?m)^# pass (\\d+)').Groups[1].Value
 $failed=[regex]::Match($report,'(?m)^# fail (\\d+)').Groups[1].Value
 $caps=@(node capabilities.test.mjs 2>&1)
 $capsExit=$LASTEXITCODE
 $ok=($testExit -eq 0 -and $capsExit -eq 0 -and $passed -match '^[1-9][0-9]*$' -and $failed -eq '0')
 [pscustomobject]@{ok=$ok;suite='mcp-regression';tested_source_sha=$source;passed=$passed;failed=$failed;capabilities_passed=($capsExit -eq 0);exit_code=$testExit} | ConvertTo-Json -Compress
 if(-not $ok){exit 1}
}finally{$mutex.ReleaseMutex();$mutex.Dispose()}`;
}
export async function runApprovedTests(env,args,execute,consume,audit){
 if(!args||args.suite!=='mcp-regression'||Object.keys(args).some(k=>!['suite','request_id'].includes(k)))throw Error('test_suite_not_allowed');
 if(!/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(args.request_id||''))throw Error('test_request_id_required');
 const command=approvedTestCommand(env.ARA_TEST_SOURCE_SHA);
 if(!await consume('mcp_regression_request',args.request_id,Math.floor(Date.now()/1000)+1800))throw Error('test_request_replayed');
 if(audit)await audit('RUNNING',args.request_id,{tested_source_sha:env.ARA_TEST_SOURCE_SHA});
 const out=await execute('shell',{command,shell:'powershell'},90);
 let shell,report;
 try{shell=JSON.parse(out.output);report=JSON.parse(String(shell.stdout||'').trim());}catch{throw Error('test_runner_invalid_response');}
 if(report.tested_source_sha!==env.ARA_TEST_SOURCE_SHA||report.suite!=='mcp-regression')throw Error('test_runner_source_mismatch');
 const ok=!!(out.ok&&shell.exit_code===0&&report.ok);
 if(audit)await audit(ok?'PROVEN':'FAILED',args.request_id,{tested_source_sha:report.tested_source_sha,passed:Number(report.passed||0),failed:Number(report.failed||0),job_id:out.job_id||null});
 return {ok,suite:report.suite,tested_source_sha:report.tested_source_sha,passed:Number(report.passed||0),failed:Number(report.failed||0),capabilities_passed:report.capabilities_passed===true,job_id:out.job_id||null};
}
