# Heartbeat adversarial QA3 — PROVEN
STATUS: PROVEN
AREA: qa / kwai-heartbeat
DATE: 2026-10-06
RUN: 37403058717
JOBS: 112074350891 ; 112074350962 ; 112074351012 ; 112074351023 ; 112074351119
SUPERSEDES: test-hub/findings/20261006-lease-five-heartbeat-adversarial-qa3.md

Five concurrent new cases all green:
- parallel-isolation: two wrappers keep job/generation/log identity isolated.
- identity-stable: initial + periodic renew preserve the same job/generation.
- external-term: TERM to wrapper produces expected signal exit behavior.
- missing-command: nonexistent child command preserves 127.
- slow-renew: slow initial renew blocks child launch; no child side effect occurs before lease validation.

No production mutation, login, Android, media publication, or anonymous YouTube extraction.
