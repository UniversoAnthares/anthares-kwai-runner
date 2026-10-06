# Control → publisher contract QA5 — PROVEN
STATUS: PROVEN
AREA: control-integration
DATE: 2026-10-06
RUN: 37405502253
JOBS: 112082057008; 112082057156; 112082057185; 112082057282; 112082057320

Five isolated boundary invariants passed:
- claim precedes publisher.
- canonical job ID propagates unchanged.
- lease_generation propagates unchanged.
- no job means no publisher invocation.
- stale generation cannot cross publisher boundary.

No real publication or Android/login mutation.
