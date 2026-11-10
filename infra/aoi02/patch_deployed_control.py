#!/usr/bin/env python3
"""AOI-02: patch the *active deployed bundle* of anthares-control, preserving Kwai.

This reads the exact multipart response from the Cloudflare Worker script API,
checks the known live v18 markers and injects a single scoped OIDC bridge into
the existing top-level fetch. It does not use older repository worker sources.
No secrets appear in this source or any command-line argument.
"""
from pathlib import Path
import hashlib
import json
import sys

BRIDGE = r'''
// AOI-02: read-only authentication gate for the existing GitLab Clipper producer.
// Media production and publication remain controlled by the existing Neon ledger.
const aoi02PinnedJwks = [{"kty":"RSA","kid":"kewiQq9jiC84CvSsJYOB-N6A8WFLSV20Mb-y7IlWDSQ","e":"AQAB","n":"5RyvCSgBoOGNE03CMcJ9Bzo1JDvsU8XgddvRuJtdJAIq5zJ8fiUEGCnMfAZI4of36YXBuBalIycqkgxrRkSOENRUCWN45bf8xsQCcQ8zZxozu0St4w5S-aC7N7UTTarPZTp4BZH8ttUm-VnK4aEdMx9L3Izo0hxaJ135undTuA6gQpK-0nVsm6tRVq4akDe3OhC-7b2h6z7GWJX1SD4sAD3iaq4LZa8y1mvBBz6AIM9co8R-vU1_CduxKQc3KxCnqKALbEKXm0mTGsXha9aNv3pLNRNs_J-cCjBpb1EXAe_7qOURTiIHdv8_sdjcFTJ0OTeLWywuSf7mD0Wpx2LKcD6ImENbyq5IBuR1e2ghnh5Y9H33cuQ0FRni8ikq5W3xP3HSMfwlayhIAJN_WnmbhENRU-m2_hDPiD9JYF2CrQneLkE3kcazSdtarPbg9ZDiydHbKWCV-X7HxxIKEr9N7P1V5HKatF4ZUrG60e3eBnRyccPwmT66i9NYyrcy1_ZNN8D1DY8xh9kflUDy4dSYu4R7AEWxNJWQQov525v0MjD5FNAS03rpk4SuW3Mt7IP73m-_BpmIhW3LZsnmfd8xHRjf0M9veyJD0--ETGmh8t3_CXh3I3R9IbcSEntUl_2lCvc_6B-m8W-t2nZr4wvOq9-iaTQXAn1Au6EaOYWvDRE","use":"sig","alg":"RS256"},{"kty":"RSA","kid":"4i3sFE7sxqNPOT7FdvcGA1ZVGGI_r-tsDXnEuYT4ZqE","e":"AQAB","n":"4cxDjTcJRJFID6UCgepPV45T1XDz_cLXSPgMur00WXB4jJrR9bfnZDx6dWqwps2dCw-lD3Fccj2oItwdRQ99In61l48MgiJaITf5JK2c63halNYiNo22_cyBG__nCkDZTZwEfGdfPRXSOWMg1E0pgGc1PoqwOdHZrQVqTcP3vWJt8bDQSOuoZBHSwVzDSjHPY6LmJMEO42H27t3ZkcYtS5crU8j2Yf-UH5U6rrSEyMdrCpc9IXe9WCmWjz5yOQa0r3U7M5OPEKD1-8wuP6_dPw0DyNO_Ei7UerVtsx5XSTd-Z5ujeB3PFVeAdtGxJ23oRNCq2MCOZBa58EGeRDLR7Q","use":"sig","alg":"RS256"},{"kty":"RSA","kid":"i3ZOa_TGMII4F39SBmXwxMok3WTPSU7kgacm4RIceio","e":"AQAB","n":"rtevzCHH0zGGwcgYFxBK00twLyHIOrD1jLyyQAD8-3QZX5JvozrkoCMFuMzdwt-6D4W4v_7PFtGolFW7ematuCYL6-NnJXUEEA_Tgz-AsbEQr0_qRQvfvkNnfvaqX_u5lCVc4Eh5HL3efQseA_mH4461B1dSzNi5DD_Mamx4CuksjrMQ2lr2AbcLg3Ip9wQYVX8a4y_uhoS2sz9bTJ9MqJ45wvfKpHK2m4pZmjSakPz6B9gLU6buVXzfx6wbhdEL1TQfvH901JnU_Scv7l70ymBpEoFtM0Vi_XvyYbkos8oc2R9o6_SXaodCHzOAZX5ujUwJZcrMdsgzBMgxItWZbQ","use":"sig","alg":"RS256"}];
let aoi02Jwks = aoi02PinnedJwks;
let aoi02JwksAt = Date.now() + 300000;
async function aoi02SignedGitLab(req) {
  const match = /^Bearer\s+(.+)$/i.exec(req.headers.get("Authorization") || "");
  const jwt = match ? match[1] : "";
  if (jwt.length < 200 || jwt.length > 16000) { console.warn("AOI02_JWT_LENGTH"); return false; }
  const parts = jwt.split(".");
  if (parts.length !== 3) return false;
  let hdr, claims;
  try {
    const decode = s => JSON.parse(atob(s.replace(/-/g, "+").replace(/_/g, "/")
      .padEnd(Math.ceil(s.length / 4) * 4, "=")));
    hdr = decode(parts[0]); claims = decode(parts[1]);
  } catch { console.warn("AOI02_JWT_DECODE"); return false; }
  const now = Math.floor(Date.now() / 1000);
  const audience = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (hdr.alg !== "RS256" || !/^[A-Za-z0-9_.-]{1,200}$/.test(hdr.kid || "")
      || claims.iss !== "https://gitlab.com"
      || !audience.includes("https://anthares-control.anthares1.workers.dev")
      || String(claims.project_id) !== "87361774"
      || claims.project_path !== "UniversoAnthares/anthares-clipper"
      || claims.sub !== "project_path:UniversoAnthares/anthares-clipper:ref_type:branch:ref:main"
      || claims.ref !== "main" || claims.ref_type !== "branch"
      || String(claims.ref_protected) !== "true"
      || !["push", "web", "schedule", "api"].includes(claims.pipeline_source)
      || !Number.isInteger(claims.exp) || claims.exp <= now || claims.exp > now + 3600
      || !Number.isInteger(claims.iat) || claims.iat > now + 60 || claims.iat < now - 600
      || (claims.nbf !== undefined && (!Number.isInteger(claims.nbf)
          || claims.nbf > now + 60))) { console.warn("AOI02_JWT_CLAIMS"); return false; }
  try {
    if (!aoi02Jwks || Date.now() > aoi02JwksAt) {
      try {
        const discovery = await fetch("https://gitlab.com/.well-known/openid-configuration",
          {signal: AbortSignal.timeout(7500)});
        if (!discovery.ok) throw Error("discovery_failed");
        const keysURL = new URL((await discovery.json()).jwks_uri);
        if (keysURL.origin !== "https://gitlab.com" || keysURL.username || keysURL.password)
          throw Error("unexpected_jwks_origin");
        const response = await fetch(keysURL.toString(), {signal: AbortSignal.timeout(7500)});
        if (!response.ok) throw Error("jwks_failed");
        const keys = (await response.json()).keys;
        if (!Array.isArray(keys)) throw Error("keys_invalid");
        aoi02Jwks = keys;
      } catch {
        aoi02Jwks = aoi02Jwks || aoi02PinnedJwks;
      }
      aoi02JwksAt = Date.now() + 300000;
    }
    const jwk = (aoi02Jwks || []).find(k => k.kid === hdr.kid && k.kty === "RSA"
      && (!k.alg || k.alg === "RS256"))
      || aoi02PinnedJwks.find(k => k.kid === hdr.kid && k.kty === "RSA"
        && (!k.alg || k.alg === "RS256"));
    if (!jwk) { console.warn("AOI02_JWT_KID_NOT_FOUND"); return false; }
    const key = await crypto.subtle.importKey("jwk", jwk,
      {name: "RSASSA-PKCS1-v1_5", hash: "SHA-256"}, false, ["verify"]);
    const bytes = s => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")
      .padEnd(Math.ceil(s.length / 4) * 4, "=")), c => c.charCodeAt(0));
    const verified = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key,
      bytes(parts[2]), new TextEncoder().encode(parts[0] + "." + parts[1]));
    if (!verified) console.warn("AOI02_JWT_SIGNATURE_FALSE");
    return verified;
  } catch (e) { console.warn("AOI02_JWT_VERIFY_ERROR:" + String(e && e.name || "Unknown").slice(0,30)); return false; }
}
async function aoi02RuntimeSecrets(req, env) {
  const reply = (status, data) => Response.json(data, {
    status,
    headers: {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
  });
  if (req.method !== "POST") return reply(405, {ok: false, error: "method_not_allowed"});
  if (!(await aoi02SignedGitLab(req))) return reply(401, {ok: false, error: "unauthorized"});
  if ((req.headers.get("content-type") || "").split(";")[0].trim().toLowerCase() !== "application/json")
    return reply(415, {ok: false, error: "invalid_content_type"});
  const length = Number(req.headers.get("content-length") || 0);
  if (length > 4096) return reply(413, {ok: false, error: "body_too_large"});
  let body;
  try { body = await req.json(); } catch { return reply(400, {ok: false, error: "invalid_json"}); }
  if (body?.scope !== "clipper-publish") return reply(403, {ok: false, error: "invalid_scope"});
  const password = env.WP_APP_PASSWORD;
  if (typeof password !== "string" || !password)
    return reply(503, {ok: false, error: "runtime_secrets_unavailable"});
  const site = "https://anthares.us", username = "lucasyahn";
  try {
    const response = await fetch(site + "/wp-json/wp/v2/users/me", {
      headers: {"Authorization": "Basic " + btoa(username + ":" + password),
        "Accept": "application/json"},
      redirect: "manual", signal: AbortSignal.timeout(9000)
    });
    if (!response.ok)
      return reply(503, {ok: false, error: "wordpress_auth_unavailable", upstream_status: response.status});
    const profile = await response.json();
    if (Number(profile?.id) !== 1)
      return reply(503, {ok: false, error: "wordpress_identity_mismatch"});
  } catch (e) { return reply(503, {ok: false, error: "wordpress_auth_transport_failed", diagnostic: String(e && e.name || "Unknown").slice(0,40), reason: (/redirect/i.test(String(e && e.message || "")) ? "redirect" : /fetch/i.test(String(e && e.message || "")) ? "fetch" : /invalid/i.test(String(e && e.message || "")) ? "invalid" : "other")}); }
  return reply(200, {ok: true, values: {
    WP_SITE_URL: site, WP_USERNAME: username, WP_APP_PASSWORD: password
  }});
}
'''

ANCHOR = '''var index_default = { ...worker, async fetch(request, env) {
  try {
    return await worker.fetch(request, env);'''
REPLACEMENT = '''var index_default = { ...worker, async fetch(request, env) {
  try {
    if (new URL(request.url).pathname === "/runtime-secrets")
      return await aoi02RuntimeSecrets(request, env);
    return await worker.fetch(request, env);'''

def extract(source: bytes) -> str:
    header, tail = source.split(b"\r\n\r\n", 1)
    assert b'Content-Disposition: form-data; name="index.js"' in header, "Unexpected worker bundle part"
    boundary = source.split(b"\r\n", 1)[0]
    assert boundary.startswith(b"--"), "Missing multipart boundary"
    closing = b"\r\n" + boundary + b"--"
    assert tail.endswith(closing + b"\r\n") or tail.endswith(closing), "Malformed bundle ending"
    cut = tail.rfind(closing)
    assert cut >= 0
    return tail[:cut].decode("utf-8")

def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_deployed_control.py <cloudflare-multipart> <output-dir>")
    src_path = Path(sys.argv[1])
    out = Path(sys.argv[2])
    raw = src_path.read_bytes()
    old = extract(raw)
    assert old.count(ANCHOR) == 1, "Exact live entrypoint must match once"
    assert "2026-10-17-physical-android-v18" in old, "Kwai active version changed"
    assert "kwai_physical_primary" in old, "Kwai routing must remain"
    assert "async scheduled(event, env, ctx)" in old, "Worker cron must remain"
    assert "export {\n  AntharesQueue," in old, "Worker Durable Object must remain"
    assert "aoi02RuntimeSecrets" not in old, "Route already installed"
    changed = old.replace(ANCHOR, BRIDGE + "\n" + REPLACEMENT)
    assert changed.count(ANCHOR) == 0 and changed.count("aoi02RuntimeSecrets(request, env)") == 1
    assert changed.count("2026-10-17-physical-android-v18") == old.count("2026-10-17-physical-android-v18")
    out.mkdir(parents=True, exist_ok=True)
    (out / "original.js").write_text(old, encoding="utf-8")
    (out / "src").mkdir(exist_ok=True)
    (out / "src" / "index.js").write_text(changed, encoding="utf-8")
    print(json.dumps({"ok": True, "original_sha256": hashlib.sha256(old.encode()).hexdigest(),
      "patched_sha256": hashlib.sha256(changed.encode()).hexdigest(),
      "old_length": len(old), "new_length": len(changed),
      "kwai_source_preserved": True, "new_route": "/runtime-secrets"}))

if __name__ == "__main__":
    main()
