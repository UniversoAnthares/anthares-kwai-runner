from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .runtime import PROGRAM_DATA, RuntimeManager

LOCK_DIR = PROGRAM_DATA / "locks"
LOCK_FILE = LOCK_DIR / "watchdog.lock"


class FileLease:
    def __init__(self, path: Path, ttl_seconds: int = 120):
        self.path = path
        self.ttl_seconds = ttl_seconds
        self.owner = f"{os.getpid()}-{int(time.time())}"

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        now = time.time()
        if self.path.exists():
            try:
                existing = json.loads(self.path.read_text(encoding="utf-8"))
                if float(existing.get("expires_at", 0)) > now:
                    return False
            except Exception:
                pass
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"owner": self.owner, "expires_at": now + self.ttl_seconds}), encoding="utf-8")
        os.replace(tmp, self.path)
        try:
            actual = json.loads(self.path.read_text(encoding="utf-8"))
            return actual.get("owner") == self.owner
        except Exception:
            return False

    def renew(self) -> None:
        if self.path.exists():
            self.path.write_text(json.dumps({"owner": self.owner, "expires_at": time.time() + self.ttl_seconds}), encoding="utf-8")

    def release(self) -> None:
        try:
            current = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
            if current.get("owner") == self.owner:
                self.path.unlink(missing_ok=True)
        except Exception:
            pass


def run_once() -> dict:
    lease = FileLease(LOCK_FILE)
    if not lease.acquire():
        return {"ok": True, "skipped": "lease_busy"}
    try:
        manager = RuntimeManager()
        status = manager.status()
        if status.get("transport_state") in {"offline", "missing"} and status.get("process_running"):
            recovery = manager.recover()
            return {"ok": bool(recovery.get("ok")), "status": status, "recovery": recovery}
        return {"ok": True, "status": status, "recovery": None}
    finally:
        lease.release()


def main() -> int:
    PROGRAM_DATA.mkdir(parents=True, exist_ok=True)
    delay = 15
    while True:
        try:
            result = run_once()
            delay = 30 if result.get("ok") else min(300, max(30, delay * 2))
        except Exception as exc:
            with (PROGRAM_DATA / "watchdog-errors.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": time.time(), "error": type(exc).__name__, "message": str(exc)}) + "\n")
            delay = min(300, max(30, delay * 2))
        time.sleep(delay)


if __name__ == "__main__":
    raise SystemExit(main())
