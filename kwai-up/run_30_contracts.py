#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "kwai-up" / "tests"


def run_case(case: int) -> tuple[int, int, str]:
    env = os.environ.copy()
    env["KWAI_UP_CASE"] = f"{case:02d}"
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(TEST_DIR), "-p", "test_*.py", "-v"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
    )
    return case, proc.returncode, proc.stdout


def main() -> int:
    results: list[tuple[int, int, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
        futures = [pool.submit(run_case, i) for i in range(1, 31)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    results.sort()
    failed = []
    for case, rc, output in results:
        marker = "PASS" if rc == 0 else "FAIL"
        print(f"KWAI_UP_CASE={case:02d} RESULT={marker}", flush=True)
        if rc != 0:
            failed.append(case)
            print(output[-5000:], flush=True)
    if failed:
        print("KWAI_UP_30_RESULT=FAIL CASES=" + ",".join(f"{x:02d}" for x in failed), flush=True)
        return 1
    print("KWAI_UP_30_RESULT=PASS CASES=30", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
