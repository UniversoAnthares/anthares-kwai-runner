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
let aoi02Jwks = null;
let aoi02JwksAt = 0;
async function aoi02SignedGitLab(req) {
  const match = /^Bearer\s+(.+)$/i.exec(req.headers.get("Authorization") || "");
  const jwt = match ? match[1] : "";
  if (jwt.length < 200 || jwt.length > 16000) return false;
  const parts = jwt.split(".");
  if (parts.length !== 3) return false;
  let hdr, claims;
  try {
    const decode = s => JSON.parse(atob(s.replace(/-/g, "+").replace(/_/g, "/")
      .padEnd(Math.ceil(s.length / 4) * 4, "=")));
    hdr = decode(parts[0]); claims = decode(parts[1]);
  } catch { return false; }
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
      || !["push", "web", "schedule"].includes(claims.pipeline_source)
      || !Number.isInteger(claims.exp) || claims.exp <= now || claims.exp > now + 3600
      || !Number.isInteger(claims.iat) || claims.iat > now + 60 || claims.iat < now - 600
      || (claims.nbf !== undefined && (!Number.isInteger(claims.nbf)
          || claims.nbf > now + 60))) return false;
  try {
    if (!aoi02Jwks || Date.now() > aoi02JwksAt) {
      const discovery = await fetch("https://gitlab.com/.well-known/openid-configuration",
        {signal: AbortSignal.timeout(7500)});
      if (!discovery.ok) return false;
      const keysURL = new URL((await discovery.json()).jwks_uri);
      if (keysURL.origin !== "https://gitlab.com" || keysURL.username || keysURL.password) return false;
      const response = await fetch(keysURL.toString(), {signal: AbortSignal.timeout(7500)});
      if (!response.ok) return false;
      const keys = (await response.json()).keys;
      if (!Array.isArray(keys)) return false;
      aoi02Jwks = keys; aoi02JwksAt = Date.now() + 300000;
    }
    const jwk = aoi02Jwks.find(k => k.kid === hdr.kid && k.kty === "RSA"
      && (!k.alg || k.alg === "RS256"));
    if (!jwk) return false;
    const key = await crypto.subtle.importKey("jwk", jwk,
      {name: "RSASSA-PKCS1-v1_5", hash: "SHA-256"}, false, ["verify"]);
    const bytes = s => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")
      .padEnd(Math.ceil(s.length / 4) * 4, "=")), c => c.charCodeAt(0));
    return await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key,
      bytes(parts[2]), new TextEncoder().encode(parts[0] + "." + parts[1]));
  } catch { return false; }
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
      redirect: "error", signal: AbortSignal.timeout(9000)
    });
    if (!response.ok)
      return reply(503, {ok: false, error: "wordpress_auth_unavailable"});
    const profile = await response.json();
    if (Number(profile?.id) !== 1)
      return reply(503, {ok: false, error: "wordpress_identity_mismatch"});
  } catch { return reply(503, {ok: false, error: "wordpress_auth_transport_failed"}); }
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
