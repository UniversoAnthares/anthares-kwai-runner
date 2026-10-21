#!/usr/bin/env node
// Gracefully close ONLY the dedicated Pinterest CDP browser after user login.
const port=9226;
const r=await fetch('http://127.0.0.1:'+port+'/json/version',{signal:AbortSignal.timeout(5000)});
if(!r.ok)throw Error('PIN_CDP_UNAVAILABLE');
const data=await r.json();
const socket=data.webSocketDebuggerUrl;
if(!/^ws:\/\/127\.0\.0\.1:9226\/devtools\/browser\/[a-zA-Z0-9-]+$/.test(socket))throw Error('PIN_CDP_WRONG_BROWSER');
const ws=new WebSocket(socket);
await new Promise((ok,no)=>{ws.onopen=ok;ws.onerror=no});
ws.send(JSON.stringify({id:1,method:'Browser.close'}));
await new Promise(ok=>{ws.onclose=ok;setTimeout(ok,3500)});
process.stdout.write('PINTEREST_CDP_CLOSED\n');
