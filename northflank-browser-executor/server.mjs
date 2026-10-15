import http from 'node:http';
import { chromium } from 'playwright';
import { timingSafeEqual } from 'node:crypto';
const port = Number(process.env.PORT || 8080);
const token = process.env.BROWSER_EXECUTOR_TOKEN;
if (!token) throw new Error('BROWSER_EXECUTOR_TOKEN must be configured');
let browser;
let context;
const equal = (a,b) => { const x=Buffer.from(a||'');const y=Buffer.from(b||'');return x.length===y.length && timingSafeEqual(x,y); };
const send = (res,status,data) => {res.writeHead(status,{'content-type':'application/json','cache-control':'no-store'});res.end(JSON.stringify(data));};
async function getContext() { if (!browser || !browser.isConnected()) browser=await chromium.launch({headless:true,args:['--no-sandbox']}); if(!context)context=await browser.newContext(); return context; }
const server=http.createServer(async(req,res)=>{
  if(req.url==='/health' && req.method==='GET')return send(res,200,{ok:true,service:'anthares-browser-executor'});
  if(!equal(req.headers.authorization,'Bearer '+token))return send(res,401,{error:'unauthorized'});
  try {
    if(req.url==='/session/start'&&req.method==='POST'){const ctx=await getContext();let page=ctx.pages()[0];if(!page)page=await ctx.newPage();await page.goto('https://www.tiktok.com/',{waitUntil:'domcontentloaded',timeout:30000});return send(res,200,{ok:true,url:page.url()});}
    if(req.url==='/session/status'&&req.method==='GET')return send(res,200,{ok:true,active:!!context,pages:context?.pages().length||0});
    if(req.url==='/session/save'&&req.method==='POST'){if(!context)return send(res,409,{error:'no_active_session'});const state=await context.storageState();return send(res,200,{ok:true,storage_state:state});}
    if(req.url==='/session/close'&&req.method==='POST'){await context?.close();context=null;await browser?.close();browser=null;return send(res,200,{ok:true});}
    return send(res,404,{error:'not_found'});
  }catch(e){return send(res,503,{ok:false,error:String(e?.message||e).slice(0,300)});}
});
server.listen(port,'0.0.0.0');
