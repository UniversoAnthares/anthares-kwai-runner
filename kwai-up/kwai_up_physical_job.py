#!/usr/bin/env python3
from __future__ import annotations

import pathlib

import kwai_up_job as job

# Keep the original transactional ledger/dedupe implementation, but route the
# publisher subprocess to the verified physical Android HID adapter.
job.SAFE = pathlib.Path(__file__).with_name("kwai_up_physical.py")

if __name__ == "__main__":
    raise SystemExit(job.main())
