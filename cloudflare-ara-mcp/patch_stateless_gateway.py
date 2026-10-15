#!/usr/bin/env python3
from pathlib import Path
import re

p = Path(__file__).with_name('src') / 'index.js'
s = p.read_text(encoding='utf-8')

old = "function st(env){return env.GATEWAY_STATE.get(env.GATEWAY_STATE.idFromName('global'));}"
new = "const _statelessStates=new WeakMap();function st(env){let x=_statelessStates.get(env);if(!x){x=new StatelessGatewayState(env);_statelessStates.set(env,x);}return x;}"
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('state accessor target missing')

marker = 'export class GatewayState extends DurableObject{'
if 'class StatelessGatewayState{' not in s:
    if marker not in s:
        raise SystemExit('GatewayState marker missing')
    cls = r'''class StatelessGatewayState{
  constructor(env){this.env=env;}
  async ensure(){
    const a=String(this.env.ARA_OAUTH_SECRET||'');
    const pr=String(this.env.ARA_SIGNING_PRIVATE_JWK||'');
    const pu=String(this.env.ARA_SIGNING_PUBLIC_JWK||'');
    if(!a||!pr||!pu)throw new Error('stateless_gateway_secrets_missing');
    let priv,pub;try{priv=JSON.parse(pr);pub=JSON.parse(pu);}catch{throw new Error('stateless_gateway_key_invalid');}
    return{priv,pub,secret:a};
  }
  async publicPem(){const {pub}=await this.ensure();const k=await crypto.subtle.importKey('jwk',pub,{name:'Ed25519'},true,['verify']);const spki=new Uint8Array(await crypto.subtle.exportKey('spki',k));const b64=btoa(String.fromCharCode(...spki));const lines=b64.match(/.{1,64}/g)||[];return `-----BEGIN PUBLIC KEY-----\n${lines.join('\n')}\n-----END PUBLIC KEY-----\n`;}
  async signControl(method,path,raw=''){const {priv}=await this.ensure();const k=await crypto.subtle.importKey('jwk',priv,{name:'Ed25519'},false,['sign']);const ts=String(Date.now());const payload=`${ts}\n${String(method).toUpperCase()}\n${path}\n${raw}`;const sig=new Uint8Array(await crypto.subtle.sign({name:'Ed25519'},k,te.encode(payload)));return{timestamp:ts,signature:b64urlBytes(sig)};}
  async hmac(input){const {secret}=await this.ensure();const k=await crypto.subtle.importKey('raw',fromB64url(secret),{name:'HMAC',hash:'SHA-256'},false,['sign']);return b64urlBytes(new Uint8Array(await crypto.subtle.sign('HMAC',k,te.encode(input))));}
  async signToken(payload){const body=b64urlBytes(te.encode(JSON.stringify(payload)));return `${body}.${await this.hmac(body)}`;}
  async verifyToken(token,type){const parts=String(token||'').split('.');if(parts.length!==2)return null;const [body,sig]=parts;if(!eq(sig,await this.hmac(body)))return null;try{const p=JSON.parse(td.decode(fromB64url(body)));if(p.typ!==type||p.iss!==ORIGIN||p.aud!==ORIGIN||!p.exp||p.exp<=Math.floor(Date.now()/1000)||!Array.isArray(p.scp))return null;return p;}catch{return null;}}
  async consume(kind,jti,exp){if(kind==='oauth_pending')return true;return consumeViaControl(this.env,kind,jti,exp);}
  async pinnedClient(){return String(this.env.ARA_PINNED_CLIENT||'');}
  async pinClient(clientId){const p=await this.pinnedClient();return !p||p===String(clientId);}
}

'''
    s = s.replace(marker, cls + marker, 1)

required = [
    'class StatelessGatewayState{',
    'stateless_gateway_secrets_missing',
    "if(kind==='oauth_pending')return true",
    'const _statelessStates=new WeakMap()',
]
for item in required:
    if item not in s:
        raise SystemExit('missing marker: '+item)

p.write_text(s, encoding='utf-8')
print('ARA_STATELESS_GATEWAY_PATCH_OK=1')
