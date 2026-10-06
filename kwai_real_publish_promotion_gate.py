#!/usr/bin/env python3
"""Fail-closed contract for promoting Kwai Real Publication to the protected publisher."""
import json, os, sys

required = {
    "KWAI_QUEUE_JOB_ID": os.getenv("KWAI_QUEUE_JOB_ID","").strip(),
    "KWAI_LEASE_GENERATION": os.getenv("KWAI_LEASE_GENERATION","").strip(),
    "KWAI_SOURCE_ID": os.getenv("KWAI_SOURCE_ID","").strip(),
    "KWAI_SOURCE_START": os.getenv("KWAI_SOURCE_START","").strip(),
    "KWAI_SOURCE_END": os.getenv("KWAI_SOURCE_END","").strip(),
}
missing=[k for k,v in required.items() if not v]
if missing:
    raise SystemExit("PROMOTION_CONTRACT_MISSING="+",".join(missing))
try:
    generation=int(required["KWAI_LEASE_GENERATION"])
    start=float(required["KWAI_SOURCE_START"]); end=float(required["KWAI_SOURCE_END"])
    if generation < 1 or end <= start: raise ValueError()
except ValueError:
    raise SystemExit("PROMOTION_CONTRACT_INVALID")
print(json.dumps({"ok":True,"job_id":required["KWAI_QUEUE_JOB_ID"],"lease_generation":generation,"source_id":required["KWAI_SOURCE_ID"],"source_start":start,"source_end":end},separators=(",",":")))
print("KWAI_REAL_PUBLISH_PROMOTION_CONTRACT_OK")
