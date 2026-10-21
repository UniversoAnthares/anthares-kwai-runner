#!/usr/bin/env python3
"""Local Pinterest queue publisher. One fenced Neon job per invocation.
Schedule this script every 5 minutes via Windows Task Scheduler.
Never stores credentials, retries uncertain posts, or publishes Buffer-reserved jobs.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT = os.getenv("CORTES_PINTEREST_ACCOUNT", "lucasyahn")
BOARD = "819514532133906920"

def main():
    os.environ.setdefault("PINTEREST_BOARD_ID", BOARD)
    if os.environ.get("CORTES_PINTEREST_LOCAL_ENABLED") != "1":
        print(json.dumps({"status":"DISABLED","reason":"CORTES_PINTEREST_LOCAL_ENABLED"}))
        return 0
    if os.environ.get("PINTEREST_BOARD_ID") != BOARD:
        print(json.dumps({"status":"BLOCKED","reason":"board_mismatch"}))
        return 2
    if os.environ.get("ANTHARES_SOCIAL_COMMIT") != "1":
        print(json.dumps({"status":"BLOCKED","reason":"live_commit_not_armed"}))
        return 2
    args=[sys.executable,str(ROOT/"tools"/"cortes_social_queue_consumer.py"),
          "--platform","pinterest","--account",ACCOUNT]
    result=subprocess.run(args,cwd=str(ROOT),timeout=900,check=False)
    return result.returncode

if __name__ == "__main__":
    raise SystemExit(main())
