import {synchronize,latest} from './lib/mirror.mjs';
const [mode='sync',ref='main',fault='']=process.argv.slice(2);
const result=mode==='status'?await latest({ref}):await synchronize({ref,fault,trigger:{type:process.env.GITHUB_ACTIONS?'github-fallback':'local-validation',workflow_run_id:process.env.GITHUB_RUN_ID||null}});
console.log(JSON.stringify(result));if(result.ok===false)process.exitCode=1;
