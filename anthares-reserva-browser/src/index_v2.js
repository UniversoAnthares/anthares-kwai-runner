import puppeteer from "@cloudflare/puppeteer";

const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
const isKwaiHost=h=>h==="kwai.com"||h.endsWith(".kwai.com");
const AAD_TEXT="anthares-reserva-kwai-auth-v1";
const b64=v=>Uint8Array.from(atob(v),c=>c.charCodeAt(0));
const pemDer=pem=>b64(String(pem||"").replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s+/g,""));

async function decryptCapsule(env){
  if(!env.RESERVA_MIGRATION_PRIVATE_KEY||!env.RESERVA_KWAI_CAPSULE) throw new Error("auth_capsule_not_configured");
  const envelope=JSON.parse(env.RESERVA_KWAI_CAPSULE);
  if(![1,2].includes(envelope.version)||envelope.alg!=="RSA-OAEP-256+A256GCM") throw new Error("auth_capsule_version_invalid");
  const pk=await crypto.subtle.importKey("pkcs8",pemDer(env.RESERVA_MIGRATION_PRIVATE_KEY),{name:"RSA-OAEP",hash:"SHA-256"},false,["decrypt"]);
  const raw=await crypto.subtle.decrypt({name:"RSA-OAEP"},pk,b64(envelope.wrapped_key));
  const ak=await crypto.subtle.importKey("raw",raw,{name:"AES-GCM"},false,["decrypt"]);
  const aad=b64(envelope.aad); if(new TextDecoder().decode(aad)!==AAD_TEXT) throw new Error("auth_capsule_aad_invalid");
  const plain=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64(envelope.nonce),additionalData:aad},ak,b64(envelope.ciphertext));
  const c=JSON.parse(new TextDecoder().decode(plain));
  if(![1,2].includes(c.version)||!Array.isArray(c.cookies)||c.cookies.length>128) throw new Error("auth_capsule_payload_invalid");
  if(c.local_storage!=null&&(typeof c.local_storage!=="object"||Array.isArray(c.local_storage)||Object.keys(c.local_storage).length>256)) throw new Error("auth_capsule_storage_invalid");
  return c;
}

function cookiesSafe(xs){return xs.filter(c=>{const h=String(c.domain||"").replace(/^\./,"").toLowerCase();return c.name&&typeof c.value==="string"&&isKwaiHost(h)}).map(c=>{const o={name:String(c.name),value:String(c.value),domain:String(c.domain),path:String(c.path||"/"),httpOnly:!!c.httpOnly,secure:!!c.secure};if(Number(c.expires)>0)o.expires=Number(c.expires);if(["Strict","Lax","None"].includes(c.sameSite))o.sameSite=c.sameSite;return o})}
function storageSafe(x){const out={};for(const [k,v] of Object.entries(x||{})){if(String(k).length<=512&&String(v).length<=32768)out[String(k)]=String(v)}return out}

async function configure(page){
  await page.setRequestInterception(true);
  page.on("request",req=>{let u;try{u=new URL(req.url())}catch{return req.abort()};if(u.protocol!=="https:")return req.abort();if(req.isNavigationRequest()&&req.frame()===page.mainFrame()&&!isKwaiHost(u.hostname))return req.abort();if(["image","media","font"].includes(req.resourceType()))return req.abort();return req.continue()});
}
async function inspect(page){return page.evaluate(()=>{const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=="none"&&s.visibility!=="hidden"};const txt=e=>((e.innerText||e.textContent||"")+" "+(e.getAttribute?.("aria-label")||"")).replace(/\s+/g," ").trim();const nodes=[...document.querySelectorAll('a[href],button,[role="button"],[role="menuitem"],input,span,div')];const login=nodes.some(e=>vis(e)&&(/^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(txt(e))||["password","tel"].includes((e.getAttribute?.("type")||"").toLowerCase())));const owner=nodes.some(e=>vis(e)&&(/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(txt(e))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(e.getAttribute?.("data-testid")||"")||/\/(profile|account)\/(edit|settings)(\/|$)/i.test(e.getAttribute?.("href")||"")));const logout=nodes.some(e=>vis(e)&&/^(log\s*out|logout|sign\s*out|sair)$/i.test(txt(e)));return{host:location.hostname.toLowerCase(),path:location.pathname.replace(/\/$/,"").toLowerCase(),login_gate:login,owner_edit:owner,logout_visible:logout,body_present:(document.body?.innerText||"").length>0}})}

async function authProbe(env){
  let browser;
  try{
    const capsule=await decryptCapsule(env),cookies=cookiesSafe(capsule.cookies),storage=storageSafe(capsule.local_storage);
    browser=await puppeteer.launch(env.BROWSER);const page=await browser.newPage();await configure(page);
    await page.goto("https://www.kwai.com/",{waitUntil:"domcontentloaded",timeout:18000});
    if(Object.keys(storage).length)await page.evaluate(s=>{for(const[k,v]of Object.entries(s))localStorage.setItem(k,v)},storage);
    if(cookies.length)await page.setCookie(...cookies);
    await page.goto("https://www.kwai.com/@lucasrosalem",{waitUntil:"domcontentloaded",timeout:18000});await new Promise(r=>setTimeout(r,2500));
    const p=await inspect(page),identity=p.host==="www.kwai.com"&&p.path==="/@lucasrosalem"&&p.owner_edit&&!p.login_gate;
    const evidence={profile_host_ok:p.host==="www.kwai.com",profile_path_ok:p.path==="/@lucasrosalem",login_gate:p.login_gate,owner_edit:p.owner_edit,logout_visible:p.logout_visible,body_present:p.body_present,local_storage_count:Object.keys(storage).length};
    if(!identity)return{ok:true,capsule_decrypted:true,cookie_count:cookies.length,local_storage_count:Object.keys(storage).length,identity_verified:false,upload_surface_verified:false,session_state:p.login_gate?"unauthenticated":"unknown",evidence};
    await page.goto("https://studio.kwai.com/",{waitUntil:"domcontentloaded",timeout:18000});await new Promise(r=>setTimeout(r,2500));
    const s=await page.evaluate(()=>{const body=(document.body?.innerText||"").slice(0,24000);const login=!!document.querySelector('input[type="password"],input[type="tel"]')||/(^|\n)\s*(log\s*in|login|sign\s*in|entrar|fazer login)\s*($|\n)/i.test(body);const file=!!document.querySelector('input[type="file"]');const upload=/upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post/i.test(body);return{host:location.hostname.toLowerCase(),login_gate:login,file_input:file,upload_control:upload}});
    const ready=s.host==="studio.kwai.com"&&!s.login_gate&&(s.file_input||s.upload_control);
    return{ok:true,capsule_decrypted:true,cookie_count:cookies.length,local_storage_count:Object.keys(storage).length,identity_verified:true,upload_surface_verified:ready,session_state:"authenticated",evidence,studio:{host_ok:s.host==="studio.kwai.com",login_gate:s.login_gate,file_input:s.file_input,upload_control:s.upload_control}};
  }catch(e){return{ok:false,identity_verified:false,upload_surface_verified:false,error:String(e?.message||e).slice(0,140)}}finally{if(browser)await browser.close().catch(()=>{})}
}

async function stateless(env){let b;try{b=await puppeteer.launch(env.BROWSER);const p=await b.newPage();await configure(p);await p.goto("https://www.kwai.com/@lucasrosalem",{waitUntil:"domcontentloaded",timeout:15000});return{ok:true,browser_started:true,host_ok:(new URL(p.url())).hostname==="www.kwai.com"}}catch(e){return{ok:false,error:String(e?.message||e).slice(0,120)}}finally{if(b)await b.close().catch(()=>{})}}

export default{async fetch(req,env){const u=new URL(req.url);if(u.pathname==="/health")return json({ok:true,service:"anthares-reserva-browser",mode:"on-demand"});if(u.pathname==="/_auth_selftest") {const r=await authProbe(env);return json(r,r.ok?200:503)}if(u.pathname==="/_selftest"){const r=await stateless(env);return json(r,r.ok?200:503)}return json({error:"not_found"},404)}};
