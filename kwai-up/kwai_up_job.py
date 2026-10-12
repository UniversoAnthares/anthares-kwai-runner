#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parent
SAFE = ROOT / "kwai_up_safe.py"


class JobError(RuntimeError):
    pass


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise JobError(f"{name}-missing")
    return value


def file_sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


@dataclass(frozen=True)
class Identity:
    job_id: str
    source_id: str
    start_ms: int
    end_ms: int
    media: pathlib.Path
    sha256: str

    @classmethod
    def from_env(cls) -> "Identity":
        job_id = env_required("KWAI_UP_JOB_ID")
        source_id = env_required("KWAI_UP_SOURCE_ID")
        media = pathlib.Path(env_required("KWAI_UP_MEDIA")).expanduser().resolve()
        if not media.is_file():
            raise JobError("KWAI_UP_MEDIA-invalid")
        try:
            start_ms = int(env_required("KWAI_UP_START_MS"))
            end_ms = int(env_required("KWAI_UP_END_MS"))
        except ValueError as exc:
            raise JobError("source-interval-invalid") from exc
        if start_ms < 0 or end_ms <= start_ms:
            raise JobError("source-interval-invalid")
        sha = file_sha256(media)
        expected = os.getenv("KWAI_UP_MEDIA_SHA256", "").strip().lower()
        if expected and expected != sha:
            raise JobError("media-sha256-mismatch")
        return cls(job_id, source_id, start_ms, end_ms, media, sha)


class Ledger:
    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), timeout=30, isolation_level=None)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY,
              source_id TEXT NOT NULL,
              start_ms INTEGER NOT NULL,
              end_ms INTEGER NOT NULL,
              media_sha256 TEXT NOT NULL,
              state TEXT NOT NULL,
              publish_requested INTEGER NOT NULL DEFAULT 0,
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL,
              detail TEXT NOT NULL DEFAULT ''
            );
            CREATE UNIQUE INDEX IF NOT EXISTS uq_kwai_up_media_sha
              ON jobs(media_sha256);
            CREATE INDEX IF NOT EXISTS ix_kwai_up_source_interval
              ON jobs(source_id, start_ms, end_ms);
            """
        )

    def reserve(self, ident: Identity) -> None:
        now = int(time.time())
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior_job = self.db.execute(
                "SELECT job_id,state FROM jobs WHERE job_id=?", (ident.job_id,)
            ).fetchone()
            if prior_job:
                raise JobError(f"job-id-already-seen:{prior_job[0]}:{prior_job[1]}")
            prior_hash = self.db.execute(
                "SELECT job_id,state FROM jobs WHERE media_sha256=?", (ident.sha256,)
            ).fetchone()
            if prior_hash:
                raise JobError(f"media-sha256-already-seen:{prior_hash[0]}:{prior_hash[1]}")
            overlap = self.db.execute(
                """
                SELECT job_id,start_ms,end_ms,state FROM jobs
                 WHERE source_id=? AND start_ms < ? AND end_ms > ?
                 ORDER BY created_at DESC LIMIT 1
                """,
                (ident.source_id, ident.end_ms, ident.start_ms),
            ).fetchone()
            if overlap:
                raise JobError(
                    f"source-interval-overlap:{overlap[0]}:{overlap[1]}-{overlap[2]}:{overlap[3]}"
                )
            self.db.execute(
                """
                INSERT INTO jobs(job_id,source_id,start_ms,end_ms,media_sha256,state,created_at,updated_at)
                VALUES(?,?,?,?,?,'RESERVED',?,?)
                """,
                (
                    ident.job_id, ident.source_id, ident.start_ms, ident.end_ms,
                    ident.sha256, now, now,
                ),
            )
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def state(self, job_id: str, state: str, detail: str = "", publish_requested: bool | None = None) -> None:
        fields = ["state=?", "detail=?", "updated_at=?"]
        args: list[object] = [state, detail[:1000], int(time.time())]
        if publish_requested is not None:
            fields.append("publish_requested=?")
            args.append(1 if publish_requested else 0)
        args.append(job_id)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            cur = self.db.execute(
                f"UPDATE jobs SET {', '.join(fields)} WHERE job_id=?", args
            )
            if cur.rowcount != 1:
                raise JobError("ledger-job-missing")
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def get(self, job_id: str) -> dict[str, object] | None:
        row = self.db.execute(
            """
            SELECT job_id,source_id,start_ms,end_ms,media_sha256,state,publish_requested,
                   created_at,updated_at,detail FROM jobs WHERE job_id=?
            """,
            (job_id,),
        ).fetchone()
        if not row:
            return None
        keys = [
            "job_id", "source_id", "start_ms", "end_ms", "media_sha256", "state",
            "publish_requested", "created_at", "updated_at", "detail",
        ]
        return dict(zip(keys, row))


def run_safe(mode: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SAFE), mode],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )
    output = proc.stdout or ""
    if output:
        print(output, end="" if output.endswith("\n") else "\n", flush=True)
    return proc.returncode, output


def ledger_path() -> pathlib.Path:
    raw = os.getenv("KWAI_UP_LEDGER", ".kwai-up/kwai-up.sqlite3").strip()
    return pathlib.Path(raw).expanduser().resolve()


def emit(state: str, **fields: object) -> None:
    tail = " ".join(f"{k.upper()}={v}" for k, v in fields.items())
    print(f"KWAI_UP_JOB_STATE={state}" + (" " + tail if tail else ""), flush=True)


def execute() -> int:
    ident = Identity.from_env()
    ledger = Ledger(ledger_path())
    ledger.reserve(ident)
    emit("RESERVED", job=ident.job_id, sha256=ident.sha256[:16])

    rc, out = run_safe("prepare")
    if rc != 0 or "KWAI_UP_STATE=READY_TO_PUBLISH" not in out:
        ledger.state(ident.job_id, "FAILED_PREPARE", out[-1000:])
        emit("FAILED_PREPARE", job=ident.job_id)
        return rc or 71
    ledger.state(ident.job_id, "READY")
    emit("READY", job=ident.job_id)

    ledger.state(ident.job_id, "COMMITTING", publish_requested=True)
    rc, out = run_safe("commit")
    if rc == 0 and "KWAI_UP_STATE=VERIFIED" in out:
        ledger.state(ident.job_id, "VERIFIED", out[-1000:], publish_requested=True)
        emit("VERIFIED", job=ident.job_id)
        return 0

    # Once commit began, an ambiguous outcome stays permanently reserved. Retrying
    # the same hash/interval would risk a duplicate post.
    ledger.state(ident.job_id, "UNCERTAIN", out[-1000:], publish_requested=True)
    emit("UNCERTAIN", job=ident.job_id)
    return rc or 90


def show() -> int:
    job_id = env_required("KWAI_UP_JOB_ID")
    row = Ledger(ledger_path()).get(job_id)
    if row is None:
        emit("MISSING", job=job_id)
        return 4
    print(json.dumps(row, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "run").strip().lower()
    try:
        if mode == "run":
            return execute()
        if mode == "show":
            return show()
        raise JobError("invalid-mode")
    except JobError as exc:
        emit("REJECTED", reason=str(exc).replace(" ", "_"))
        return 65
    except sqlite3.IntegrityError as exc:
        emit("REJECTED", reason="ledger-integrity")
        return 66
    except Exception as exc:
        emit("FAILED", reason=type(exc).__name__)
        return 79


if __name__ == "__main__":
    raise SystemExit(main())
