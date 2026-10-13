import puppeteer from "@cloudflare/puppeteer";

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});
const sameSecret = (a, b) => {
  if (!a || !b || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
};
const isKwaiHost = host => host === "kwai.com" || host.endsWith(".kwai.com");
const AAD_TEXT = "anthares-reserva-kwai-auth-v1";
const bytesFromB64 = value => Uint8Array.from(atob(value), c => c.charCodeAt(0));
const pemToDer = pem => {
  const body = String(pem || "").replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\s+/g, "");
  if (!body) throw new Error("migration_private_key_missing");
  return bytesFromB64(body);
};

async function decryptCapsule(env) {
  if (!env.RESERVA_MIGRATION_PRIVATE_KEY || !env.RESERVA_KWAI_CAPSULE)
    throw new Error("auth_capsule_not_configured");
  const envelope = JSON.parse(env.RESERVA_KWAI_CAPSULE);
  if (envelope.version !== 1 || envelope.alg !== "RSA-OAEP-256+A256GCM")
    throw new Error("auth_capsule_version_invalid");
  const privateKey = await crypto.subtle.importKey(
    "pkcs8", pemToDer(env.RESERVA_MIGRATION_PRIVATE_KEY),
    { name: "RSA-OAEP", hash: "SHA-256" }, false, ["decrypt"]
  );
  const rawAes = await crypto.subtle.decrypt({ name: "RSA-OAEP" }, privateKey, bytesFromB64(envelope.wrapped_key));
  const aesKey = await crypto.subtle.importKey("raw", rawAes, { name: "AES-GCM" }, false, ["decrypt"]);
  const aad = bytesFromB64(envelope.aad);
  if (new TextDecoder().decode(aad) !== AAD_TEXT) throw new Error("auth_capsule_aad_invalid");
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: bytesFromB64(envelope.nonce), additionalData: aad }, aesKey, bytesFromB64(envelope.ciphertext)
  );
  const capsule = JSON.parse(new TextDecoder().decode(plaintext));
  if (capsule.version !== 1 || !Array.isArray(capsule.cookies) || capsule.cookies.length > 128)
    throw new Error("auth_capsule_payload_invalid");
  return capsule;
}

function safeCookies(cookies) {
  return cookies.filter(c => {
    const host = String(c.domain || "").replace(/^\./, "").toLowerCase();
    return c.name && typeof c.value === "string" && isKwaiHost(host);
  }).map(c => {
    const out = { name:String(c.name), value:String(c.value), domain:String(c.domain), path:String(c.path||"/"), httpOnly:!!c.httpOnly, secure:!!c.secure };
    if (Number(c.expires) > 0) out.expires = Number(c.expires);
    if (["Strict", "Lax", "None"].includes(c.sameSite)) out.sameSite = c.sameSite;
    return out;
  });
}

async function configurePage(page) {
  await page.setRequestInterception(true);
  page.on("request", req => {
    let dest;
    try { dest = new URL(req.url()); } catch { return req.abort(); }
    if (dest.protocol !== "https:") return req.abort();
    // Top-level navigation remains pinned to Kwai, while HTTPS API/static
    // subresources may load from CDN/vendor hosts required by the real UI.
    if (req.isNavigationRequest() && req.frame() === page.mainFrame() && !isKwaiHost(dest.hostname)) return req.abort();
    if (["image", "media", "font"].includes(req.resourceType())) return req.abort();
    return req.continue();
  });
}

async function inspectProfile(page) {
  return page.evaluate(() => {
    const visible = el => { const r=el.getBoundingClientRect(),s=getComputedStyle(el); return r.width>0&&r.height>0&&s.display!=="none"&&s.visibility!=="hidden"; };
    const text = el => ((el.innerText||el.textContent||"")+" "+(el.getAttribute?.("aria-label")||"")).replace(/\s+/g," ").trim();
    const body=(document.body?.innerText||"").slice(0,24000);
    const nodes=[...document.querySelectorAll('a[href],button,[role="button"],[role="menuitem"],input,span,div')];
    const login=nodes.some(el=>visible(el)&&(/^(log\s*in|login|sign\s*in|entrar|fazer login)$/i.test(text(el))||["password","tel"].includes((el.getAttribute?.("type")||"").toLowerCase())));
    const owner=nodes.some(el=>visible(el)&&(/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(text(el))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(el.getAttribute?.("data-testid")||"")||/\/(profile|account)\/(edit|settings)(\/|$)/i.test(el.getAttribute?.("href")||"")));
    const logout=nodes.some(el=>visible(el)&&/^(log\s*out|logout|sign\s*out|sair)$/i.test(text(el)));
    const exactLink=nodes.some(el=>{ if(el.tagName!=="A") return false; try { const u=new URL(el.getAttribute("href")||"",location.href); return (u.hostname==="www.kwai.com"||u.hostname==="kwai.com")&&u.pathname.replace(/\/$/,"").toLowerCase()==="/@lucasrosalem"; } catch { return false; }});
    return {host:location.hostname.toLowerCase(),path:location.pathname.replace(/\/$/,"").toLowerCase(),login_gate:login,owner_edit:owner,logout_visible:logout,exact_profile_link:exactLink,body_present:body.length>0};
  });
}

async function runProbe(env, handle) {
  let browser;
  try {
    browser = await puppeteer.launch(env.BROWSER);
    const page = await browser.newPage(); await configurePage(page);
    await page.goto("https://www.kwai.com/@"+encodeURIComponent(handle),{waitUntil:"domcontentloaded",timeout:15000});
    await new Promise(r=>setTimeout(r,1500));
    const p=await inspectProfile(page);
    return {ok:true,mode:"isolated_ephemeral",profile:{host_ok:p.host==="www.kwai.com",path_ok:p.path==="/@"+handle.toLowerCase(),login_gate:p.login_gate,owner_edit:p.owner_edit},identity_verified:false,upload_verified:false,reason:"ephemeral_browser_has_no_production_login"};
  } catch(err) { return {ok:false,error:"browser_probe_failed",detail:String(err?.message||err).slice(0,120)}; }
  finally { if(browser) await browser.close().catch(()=>{}); }
}

async function runAuthenticatedProbe(env) {
  let browser;
  try {
    const capsule=await decryptCapsule(env), cookies=safeCookies(capsule.cookies);
    if(!cookies.length) throw new Error("auth_capsule_has_no_kwai_cookies");
    browser=await puppeteer.launch(env.BROWSER);
    const page=await browser.newPage(); await configurePage(page); await page.setCookie(...cookies);
    await page.goto("https://www.kwai.com/@lucasrosalem",{waitUntil:"domcontentloaded",timeout:18000});
    await new Promise(r=>setTimeout(r,2500));
    const profile=await inspectProfile(page);
    const identity=profile.host==="www.kwai.com"&&profile.path==="/@lucasrosalem"&&profile.owner_edit&&!profile.login_gate;
    const evidence={profile_host_ok:profile.host==="www.kwai.com",profile_path_ok:profile.path==="/@lucasrosalem",login_gate:profile.login_gate,owner_edit:profile.owner_edit,logout_visible:profile.logout_visible,exact_profile_link:profile.exact_profile_link,body_present:profile.body_present};
    if(!identity) return {ok:true,capsule_decrypted:true,cookie_count:cookies.length,identity_verified:false,upload_surface_verified:false,session_state:profile.login_gate?"unauthenticated":"unknown",evidence};
    await page.goto("https://studio.kwai.com/",{waitUntil:"domcontentloaded",timeout:18000}); await new Promise(r=>setTimeout(r,2500));
    const studio=await page.evaluate(()=>{const body=(document.body?.innerText||"").slice(0,24000);const login=!!document.querySelector('input[type="password"],input[type="tel"]')||/(^|\n)\s*(log\s*in|login|sign\s*in|entrar|fazer login)\s*($|\n)/i.test(body);const file=!!document.querySelector('input[type="file"]');const upload=/upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post/i.test(body);return {host:location.hostname.toLowerCase(),login_gate:login,file_input:file,upload_control:upload,body_present:body.length>0};});
    const uploadReady=studio.host==="studio.kwai.com"&&!studio.login_gate&&(studio.file_input||studio.upload_control);
    return {ok:true,capsule_decrypted:true,cookie_count:cookies.length,identity_verified:true,upload_surface_verified:uploadReady,session_state:"authenticated",evidence,studio:{host_ok:studio.host==="studio.kwai.com",login_gate:studio.login_gate,file_input:studio.file_input,upload_control:studio.upload_control,body_present:studio.body_present}};
  } catch(err) { return {ok:false,identity_verified:false,upload_surface_verified:false,error:String(err?.message||err).slice(0,120)}; }
  finally { if(browser) await browser.close().catch(()=>{}); }
}

export default { async fetch(request,env) {
  const url=new URL(request.url);
  if(url.pathname==="/health"&&request.method==="GET") return json({ok:true,service:"anthares-reserva-browser",mode:"on-demand",authenticated_session:"not_verified"});
  const supplied=(request.headers.get("authorization")||"").replace(/^Bearer /i,"");
  if(!sameSecret(supplied,env.ANTHARES_RESERVA_TOKEN)) return json({error:"unauthorized"},401);
  if(url.pathname==="/_selftest"&&request.method==="GET"){const r=await runProbe(env,"lucasrosalem");return json({ok:r.ok,browser_started:r.ok,host_ok:r.profile?.host_ok===true,mode:r.mode||"isolated_ephemeral"},r.ok?200:503);}
  if(url.pathname==="/_auth_selftest"&&request.method==="GET"){const r=await runAuthenticatedProbe(env);return json(r,r.ok?200:503);}
  if(url.pathname!=="/probe"||request.method!=="POST") return json({error:"not_found"},404);
  let body; try{body=await request.json();}catch{return json({error:"invalid_json"},400);} const handle=String(body?.handle||"").replace(/^@/,""); if(!/^[a-zA-Z0-9._-]{1,40}$/.test(handle)) return json({error:"invalid_handle"},400); const r=await runProbe(env,handle); return json(r,r.ok?200:503);
}};
