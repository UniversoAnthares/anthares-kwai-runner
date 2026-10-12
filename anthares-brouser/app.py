import os
from pathlib import Path

import psutil
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI(title="Anthares-brouser control API", version="0.1.0")
PROFILE_DIR = Path(os.environ.get("CHROME_PROFILE_DIR", "/data/chrome-profile"))
CONTROL_TOKEN = os.environ.get("CONTROL_TOKEN", "")


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not CONTROL_TOKEN:
        raise HTTPException(status_code=503, detail="CONTROL_TOKEN not configured")
    if authorization != f"Bearer {CONTROL_TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


def chromium_processes() -> list[int]:
    pids: list[int] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmd = " ".join(proc.info.get("cmdline") or []).lower()
            if "chromium" in name or "chromium" in cmd or "chrome" in name:
                pids.append(int(proc.info["pid"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(set(pids))


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "profile_dir_exists": PROFILE_DIR.exists(),
        "chromium_running": bool(chromium_processes()),
    }


@app.get("/status")
def status(_: None = Depends(require_token)) -> dict:
    size = 0
    if PROFILE_DIR.exists():
        for path in PROFILE_DIR.rglob("*"):
            try:
                if path.is_file():
                    size += path.stat().st_size
            except OSError:
                pass
    return {
        "profile_dir": str(PROFILE_DIR),
        "profile_dir_exists": PROFILE_DIR.exists(),
        "profile_bytes": size,
        "chromium_pids": chromium_processes(),
        "session_claim": "not_verified",
    }
