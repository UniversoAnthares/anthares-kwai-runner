#!/usr/bin/env python3
from __future__ import annotations

import pathlib

import kwai_up_job as job

job.SAFE = pathlib.Path(__file__).with_name("kwai_up_physical_entry.py")

if __name__ == "__main__":
    raise SystemExit(job.main())
