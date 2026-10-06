# Five-way Kwai adversarial QA proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37402246471
COMMIT: 46e949ea0d6d829acedbc76c71b4b60138668550
SUPERSEDES: test-hub/findings/20261006-0155-lease-kwai-fiveway-adversarial.md
LEASE_AREA: kwai-qa-adversarial
LEASE_CLOSED: 2026-10-06T02:04:00Z

## Resultado
Five independent matrix jobs passed concurrently:
1. ready-proof-tamper: mismatched READY proof exits 77 before PUBLISH_REQUESTED.
2. complete-ack-loss: post-commit central complete rejection remains UNCERTAIN and cannot become confirmed/retry-safe.
3. verifier-evidence-loss: missing specific confirmation evidence invokes uncertain handling.
4. heartbeat-renew-loss: renew loss kills the child and emits FAILED_SAFE lease-heartbeat-lost.
5. reconcile-no-republish: reconciler contains verifier+reconcile only and no publisher/PUBLISH_REQUESTED path.

## Harness note
Run 37402202078 was HARNESS_INVALID because embedded heredocs broke workflow YAML before jobs were created. It is not product evidence. The corrected matrix run 37402246471 is the valid evidence.

## Consequência
These five adversarial boundaries add no remaining implementation blocker to CHAT 2. Real Android canary remains dependent on authenticated READY from kwai-login.
