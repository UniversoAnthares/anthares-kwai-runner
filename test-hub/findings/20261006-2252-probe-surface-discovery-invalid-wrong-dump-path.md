# Surface discovery probe INVALID — dump path mismatch produced empty trees
STATUS: FAILED
AREA: kwai-login
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37563219355
JOB: probe
COMMIT: 4336a79
SUPERSEDES: none

## Objetivo
Classify the outcome of run 37563219355 (Kwai Login Surface Discovery Probe) before anyone treats it as the lease's FAILURE_SIGNAL.

## Resultado
TEST_VALIDITY=INVALID. The probe never read a single UI tree: `kwai_login_surface_probe.py::dump()` shells `uiautomator dump /sdcard/kwai-login-probe.xml` but then `cat /sdcard/kwai-login.xml` — a different, stale file. Parse fails, `nodes()` returns [], so all 22 phases logged `state=OTHER editables=0 login_like=0`. The zero-node result is a harness artifact, not evidence that the login surface is unreachable. Secondary defect: the JSON log was written to `$RUNNER_TEMP` while the artifact path points at the repo root, so `kwai-login-probe-log.json` was never uploaded ("No files were found").

## Evidência decisiva
Log: 22 consecutive `[PROBE] ... editables=0 login_like=0` with state=OTHER in every phase; `No files were found with the provided path: kwai-login-probe-log.json`. Code lines 11-12 of kwai_login_surface_probe.py (dump to `kwai-login-probe.xml`, cat `kwai-login.xml`).

## Consequência
- Do NOT promote this run to the lease FAILURE_SIGNAL ("zero editable nodes in all phases") — the probe produced no observations at all.
- Do NOT implement a new session/bootstrap mechanism on the basis of this run.
- Causal repair required before re-run: read back the exact file that was dumped (or use `cat` of the same path), verify `root is not None` and abort loudly with TEST_VALIDITY=INVALID when the tree is empty, and write the log where the artifact path expects it.
- Combine with the preparation-gate finding (20261006-2241): the interactive run also showed Kwai blocked at a 5% resource-download modal, which state_from_text() must recognize ("skip the preparation" / "sorry, the internet's a bit slow") as RESOURCE_LOADING-like instead of OTHER.
- kwai-login lease 20261007-lease-kwai-login-surface-discovery.md remains authoritative; this is a read-only classification.
