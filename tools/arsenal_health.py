#!/usr/bin/env python3
"""Anthares global health check. No secrets are printed or persisted."""
import json, os, shutil, subprocess, sys, urllib.request, urllib.error
from datetime import datetime, timezone

SERVICES = {
 "github": {"kind":"http","target":"https://api.github.com/zen"},
 "cloudflare": {"kind":"env_http","env":"ANTHARES_CLOUDFLARE_HEALTH_URL"},
 "render": {"kind":"env_http","env":"ANTHARES_RENDER_HEALTH_URL"},
 "circleci": {"kind":"env_http","env":"ANTHARES_CIRCLECI_HEALTH_URL","auth_env":"CIRCLECI_TOKEN"},
 "wordpress": {"kind":"env_http","env":"ANTHARES_WORDPRESS_HEALTH_URL"},
 "telegram": {"kind":"env_http","env":"ANTHARES_TELEGRAM_HEALTH_URL"},
 "kwai": {"kind":"env_http","env":"ANTHARES_KWAI_HEALTH_URL"},
 "tiktok": {"kind":"env_http","env":"ANTHARES_TIKTOK_HEALTH_URL"},
 "instagram": {"kind":"env_http","env":"ANTHARES_INSTAGRAM_HEALTH_URL"},
 "threads": {"kind":"env_http","env":"ANTHARES_THREADS_HEALTH_URL"},
 "x": {"kind":"env_http","env":"ANTHARES_X_HEALTH_URL"},
 "gitlab": {"kind":"env_http","env":"ANTHARES_GITLAB_HEALTH_URL"},
 "codeberg": {"kind":"env_http","env":"ANTHARES_CODEBERG_HEALTH_URL"},
 "ai_commander": {"kind":"external","state":"UNKNOWN"},
 "remote_desktop_commander": {"kind":"external","state":"UNKNOWN"},
 "meshcentral": {"kind":"env_http","env":"ANTHARES_MESHCENTRAL_HEALTH_URL"},
 "winremote": {"kind":"env_http","env":"ANTHARES_WINREMOTE_HEALTH_URL"},
 "claude": {"kind":"env_http","env":"ANTHARES_CLAUDE_HEALTH_URL"},
 "grok": {"kind":"env_http","env":"ANTHARES_GROK_HEALTH_URL"},
 "perplexity": {"kind":"env_http","env":"ANTHARES_PERPLEXITY_HEALTH_URL"},
 "gemini": {"kind":"env_http","env":"ANTHARES_GEMINI_HEALTH_URL"},
 "manus": {"kind":"env_http","env":"ANTHARES_MANUS_HEALTH_URL"},
}

def probe_http(url, auth_env=None):
    if not url:
        return "AUTH_REQUIRED" if auth_env and not os.getenv(auth_env) else "UNKNOWN", "probe_not_configured"
    headers={"User-Agent":"anthares-health/1"}
    token=os.getenv(auth_env) if auth_env else None
    if auth_env and not token:
        return "AUTH_REQUIRED", "credential_not_configured"
    if token:
        headers["Authorization"]="Bearer "+token
    try:
        req=urllib.request.Request(url,headers=headers)
        with urllib.request.urlopen(req,timeout=12) as r:
            code=r.getcode()
            return ("UP" if 200 <= code < 400 else "DEGRADED"), f"http_{code}"
    except urllib.error.HTTPError as e:
        if e.code in (401,403):
            return "AUTH_REQUIRED", f"http_{e.code}"
        return "DOWN", f"http_{e.code}"
    except Exception as e:
        return "DOWN", type(e).__name__

def main():
    out={"checked_at":datetime.now(timezone.utc).isoformat(),"services":{}}
    for name,cfg in SERVICES.items():
        if cfg["kind"]=="http":
            state,evidence=probe_http(cfg["target"])
        elif cfg["kind"]=="env_http":
            state,evidence=probe_http(os.getenv(cfg["env"]),cfg.get("auth_env"))
        else:
            state,evidence=cfg.get("state","UNKNOWN"),"checked_outside_ci"
        out["services"][name]={"state":state,"evidence":evidence}
    print(json.dumps(out,indent=2,sort_keys=True))
    bad=[n for n,v in out["services"].items() if v["state"]=="DOWN"]
    return 2 if bad else 0

if __name__=="__main__":
    raise SystemExit(main())
