import asyncio
import hashlib
import hmac
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

TOKEN = os.getenv("ANTHARES_RESERVA_TOKEN", "")
DB_PATH = Path(os.getenv("ANTHARES_RESERVA_DB", "/data/anthares-reserva.sqlite3"))
PROVIDERS_JSON = os.getenv("ANTHARES_PROVIDER_CONFIG", "[]")
CIRCUIT_SECONDS = int(os.getenv("ANTHARES_CIRCUIT_SECONDS", "180"))

app = FastAPI(title="Anthares Reserva Router", docs_url=None, redoc_url=None)
router_lock = asyncio.Lock()
circuit: dict[str, float] = {}


class Dispatch(BaseModel):
    job_id: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    generation: int = Field(ge=1)
    account: str = Field(default="lucasrosalem", min_length=1, max_length=40)
    operation: str = Field(default="kwai.readonly_probe", pattern=r"^kwai\.readonly_probe$")


def auth(header: str | None):
    if not TOKEN:
        raise HTTPException(503, "router_not_configured")
    supplied = (header or "").removeprefix("Bearer ")
    if not hmac.compare_digest(TOKEN, supplied):
        raise HTTPException(401, "unauthorized")


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS jobs(job_id TEXT PRIMARY KEY,generation INTEGER NOT NULL,account TEXT NOT NULL,provider TEXT,status TEXT NOT NULL,result TEXT,updated INTEGER NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS generations(account TEXT PRIMARY KEY,generation INTEGER NOT NULL)")
    return conn


def providers() -> list[dict[str, Any]]:
    try:
        values = json.loads(PROVIDERS_JSON)
    except Exception as exc:
        raise HTTPException(503, "provider_config_invalid") from exc
    if not isinstance(values, list):
        raise HTTPException(503, "provider_config_invalid")
    safe = []
    for p in values:
        if not isinstance(p, dict) or not p.get("name") or not p.get("url"):
            continue
        if p.get("enabled", True) is not True:
            continue
        if not str(p["url"]).startswith("https://") and not str(p["url"]).startswith("http://127.0.0.1"):
            continue
        safe.append(p)
    return sorted(safe, key=lambda p: int(p.get("priority", 100)))


def public_provider_state():
    now = time.time()
    return [{"name": p["name"], "kind": p.get("kind", "native"), "priority": p.get("priority", 100), "circuit_open": circuit.get(p["name"], 0) > now} for p in providers()]


@app.get("/health")
def health():
    return {"ok": True, "service": "anthares-reserva-router"}


@app.get("/v1/providers")
def list_providers(authorization: str | None = Header(default=None)):
    auth(authorization)
    return {"ok": True, "providers": public_provider_state()}


async def preflight(client: httpx.AsyncClient, p: dict[str, Any]) -> bool:
    if circuit.get(p["name"], 0) > time.time():
        return False
    try:
        url = str(p["url"]).rstrip("/") + ("/health" if p.get("kind", "native") == "native" else "/health")
        r = await client.get(url, timeout=4)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    circuit[p["name"]] = time.time() + CIRCUIT_SECONDS
    return False


async def dispatch_once(client: httpx.AsyncClient, p: dict[str, Any], req: Dispatch) -> dict[str, Any]:
    name, kind = str(p["name"]), str(p.get("kind", "native"))
    token = os.getenv(str(p.get("token_env", "")), "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    base = str(p["url"]).rstrip("/")
    try:
        if kind == "native":
            r = await client.post(base + "/v1/probe", headers=headers, json={"job_id": req.job_id, "generation": req.generation, "handle": req.account}, timeout=55)
        elif kind == "cloudflare_legacy":
            # Read-only legacy adapter. Never use it for side-effecting operations.
            r = await client.get(base + "/_auth_selftest", headers=headers, timeout=45)
        else:
            return {"ok": False, "provider": name, "error": "unsupported_provider_kind", "definitive": True}
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        # Request outcome may be ambiguous once bytes have left this process.
        # Never fail over automatically after such an error.
        circuit[name] = time.time() + CIRCUIT_SECONDS
        return {"ok": False, "provider": name, "error": "ambiguous_transport_failure", "definitive": False, "detail": exc.__class__.__name__}
    if r.status_code >= 500 or r.status_code == 429:
        circuit[name] = time.time() + CIRCUIT_SECONDS
    try:
        body = r.json()
    except Exception:
        body = {"error": "non_json_response"}
    return {"ok": r.status_code < 400 and bool(body.get("ok", False)), "provider": name, "http_status": r.status_code, "definitive": True, "result": body}


@app.post("/v1/dispatch")
async def dispatch(req: Dispatch, authorization: str | None = Header(default=None)):
    auth(authorization)
    if not req.account.replace("_", "").replace("-", "").replace(".", "").isalnum():
        raise HTTPException(400, "invalid_account")
    async with router_lock:
        with db() as conn:
            row = conn.execute("SELECT status,result,provider,generation FROM jobs WHERE job_id=?", (req.job_id,)).fetchone()
            if row:
                payload = json.loads(row[1]) if row[1] else None
                return {"ok": row[0] == "done", "cached": True, "provider": row[2], "generation": row[3], "result": payload}
            current = conn.execute("SELECT generation FROM generations WHERE account=?", (req.account,)).fetchone()
            if current and req.generation < current[0]:
                raise HTTPException(409, "stale_generation")
            conn.execute("INSERT INTO generations(account,generation) VALUES(?,?) ON CONFLICT(account) DO UPDATE SET generation=max(generation,excluded.generation)", (req.account, req.generation))
            conn.execute("INSERT INTO jobs(job_id,generation,account,provider,status,result,updated) VALUES(?,?,?,?,?,?,?)", (req.job_id,req.generation,req.account,"","selecting",None,int(time.time())))
            conn.commit()

        async with httpx.AsyncClient(follow_redirects=False) as client:
            selected = None
            for p in providers():
                if await preflight(client, p):
                    selected = p
                    break
            if selected is None:
                result = {"ok": False, "error": "no_healthy_provider", "definitive": True}
            else:
                with db() as conn:
                    conn.execute("UPDATE jobs SET provider=?,status=?,updated=? WHERE job_id=?", (selected["name"],"dispatched",int(time.time()),req.job_id)); conn.commit()
                # Exactly one provider receives this job. No post-dispatch failover.
                result = await dispatch_once(client, selected, req)

        status = "done" if result.get("ok") else ("ambiguous" if result.get("definitive") is False else "failed")
        with db() as conn:
            conn.execute("UPDATE jobs SET status=?,result=?,updated=? WHERE job_id=?", (status,json.dumps(result,separators=(",",":")),int(time.time()),req.job_id)); conn.commit()
        return {"ok": result.get("ok", False), "cached": False, "status": status, "result": result}
