import {synchronize,latest} from './lib/mirror.mjs';
const [mode='sync',ref='main',fault='']=process.argv.slice(2);
const result=mode==='status'?await latest({ref}):await synchronize({ref,fault,trigger:{type:'local-validation'}});
console.log(JSON.stringify(result));if(result.ok===false)process.exitCode=1;
