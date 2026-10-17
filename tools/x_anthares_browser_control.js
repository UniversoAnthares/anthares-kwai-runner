const port=Number(process.env.ANTHARES_X_BROWSER_PORT||9224);
async function targets(){return await (await fetch(`http://127.0.0.1:${port}/json`)).json()}
async function target(){const ts=await targets();const p=ts.find(x=>x.type==='page'&&(x.url.startsWith('https://x.com/')||x.url.startsWith('https://twitter.com/')))||ts.find(x=>x.type==='page');if(!p)throw new Error('no_page_target');return p}
async function cdp(method,params={}){const t=await target();const ws=new WebSocket(t.webSocketDebuggerUrl);let id=1;return await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{try{ws.close()}catch{};reject(new Error('cdp_timeout'))},20000);ws.onopen=()=>ws.send(JSON.stringify({id,method,params}));ws.onerror=()=>{clearTimeout(timer);reject(new Error('websocket_error'))};ws.onmessage=e=>{let m;try{m=JSON.parse(e.data)}catch{return}if(m.id===id){clearTimeout(timer);ws.close();if(m.error)reject(new Error(m.error.message));else resolve(m.result||{})}}})}
async function evalJS(expr){const r=await cdp('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true,userGesture:true});if(r.exceptionDetails)throw new Error('evaluation_failed');return r.result?.value}
(async()=>{const [cmd,...rest]=process.argv.slice(2);let out;
if(cmd==='status'){const t=await target();out={ok:true,url:t.url,title:t.title,profile:'AntharesXBridge',headless:false,hidden_surface:true,port}}
else if(cmd==='navigate'){await cdp('Page.navigate',{url:rest[0]});await new Promise(r=>setTimeout(r,2200));out={ok:true,url:await evalJS('location.href'),title:await evalJS('document.title')}}
else if(cmd==='page'){out={ok:true,url:await evalJS('location.href'),title:await evalJS('document.title'),text:(await evalJS('document.body?document.body.innerText:""')||'').slice(0,20000)}}
else if(cmd==='eval'){out={ok:true,value:await evalJS(rest.join(' '))}}
else if(cmd==='upload'){const sel=rest[0],path=rest.slice(1).join(' ');if(!sel||!path)throw new Error('upload_requires_selector_and_path');const d=await cdp('DOM.getDocument',{depth:-1,pierce:true});const q=await cdp('DOM.querySelector',{nodeId:d.root.nodeId,selector:sel});if(!q.nodeId)throw new Error('file_input_not_found');await cdp('DOM.setFileInputFiles',{nodeId:q.nodeId,files:[path]});out={ok:true,selector:sel,file:path}}
else throw new Error('unknown_command');console.log(JSON.stringify(out));
})().catch(e=>{console.error(JSON.stringify({ok:false,error:e.message}));process.exit(1)});
