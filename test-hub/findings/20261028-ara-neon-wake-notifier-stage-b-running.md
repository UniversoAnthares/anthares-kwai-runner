# ARA wake-only notifier — Stage B preproduction
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization
DATE: 2026-10-28
RUN: CI pending
JOB: none
COMMIT: feature/ara-wake-hibernation-20261028
SUPERSEDES: none

## BASELINE_PROVEN
Stage A offline CI run 40760638379 PASS. Canonical Vercel router
createJob returns an INSERT/UPSERT row from Neon; its existing 2-second
polling and 60-second heartbeat remain in production unchanged.
Actual device agent binary C8 and private issue queues are active.

## FAILED_AVOIDED
No Cloudflare deployment; no secret or Vercel variable; no production deploy.
Do not create a second job during wake retries, and do not mark notification
success as proof of command execution. No synthetic real dispatch.

## SUCCESS_SIGNAL
Offline tests confirm notifier disabled-by-default never accesses network;
HMAC signature matches Worker protocol; target URL is fixed, no args/jobs
exposed, failure and delivered=0 cannot claim delivery, 401/403/429 handled.
Router source remains parseable and only sends wake after Neon UPSERT resolves.

## FAILURE_SIGNAL
JS syntax/unit failure, a changed live router/base/ref, any unhandled exception
from a notify timeout or a failure to keep disabled path unchanged.

## TEST_VALIDITY
Source and CI only. No Cloudflare delivery, production dispatch, low-latency
wake, Windows cutover, autosuspend or CU savings have been tested.
