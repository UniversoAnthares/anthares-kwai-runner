# 9Router free Claude runner — harmless readiness timeout
STATUS: PARTIAL
AREA: anthares-collab-router-bootstrap
DATE: 2026-10-20
SUPERSEDES: test-hub/findings/20261020-router-boot-retry-lease.md
BASELINE: 39352658418 passed live original Claude Free; 39355978335 owner-created Issue #227 passed delegated actor validation but real router probe timed out.
RUN_FAILED: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39355978335
RUN_TESTS: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39356396198
RUN_PR_STATIC: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39356396224
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/229
LEASE_STATE: CLOSED AFTER VALIDATED PR; POST-MERGE LIVE ACCEPTANCE STILL REQUIRED

## Causal failure
During the first real ChatGPT Issue #227, all three Gemini model direct probes returned PASS, the delegated GitHub Action bot actor was verified against owner-created issue and deterministic request ID. However 9Router combo bootstrap's one 40-second streaming inference request timed out: `ANTHARES_FREE_BOOTSTRAP_ERROR=ROUTER_INFERENCE_FAILED_HTTP_0`, `ROUTER_INFERENCE_TRANSPORT=TIMEOUT`. This does not refute the owner-to-bot-to-cloud bridge, nor prove generated Claude Code output.

The issue gateway posted `[ANTHARES-COLLAB] COMPLETED id=d4331069-f922-58e4-a9dc-bab1a0945bb3 conclusion=failure` with run link; it did NOT re-dispatch the same issue. Correct at-most-once behavior.

## Change & regression
Bootstrap probe `Responda OK.` only now permits up to 3 attempts, retrying only network timeout/abort or 429/502/503/504 HTTP, with 40s first and 22s later attempts. The response still MUST contain real assistant-generated text. Any 400 or empty 200 fails immediately. Actual user task is not automatically retried or duplicated; all routing provider scopes and secrets preserved. Unit tests assert timeout then real valid generated text and denial of false positives.
CI `39356396198`: existing Claude Code runner static-check success; execute skipped for PR. `39356396224`: static checks success, real model steps intentionally skipped on PR. Not a live rerun.

## Pending
Merge PR #229 after security validation, then create a NEW benign owner issue (not #227) to prove remote router inference + generated Claude Code artifact + issue completion. If Gemini quotas/timeouts continue, record PROVEN bridge/PARTIAL model and avoid blind retries. Work mode requires separate owner-started Work session to prove consumption.
