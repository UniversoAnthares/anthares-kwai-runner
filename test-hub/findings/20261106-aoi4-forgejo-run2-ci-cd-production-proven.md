# AOI item fixo 4 — Forgejo principal CI/CD: terminal production proof
STATUS: DONE
AREA: architecture/forgejo-main-ci-cd
ITEMS: [4]
DATE_UTC: 2026-11-06T02:22:50Z
OWNER: chatgpt-aoi4-forgejo-run2-proof-20261106
LEASE: CLOSED; read-only verification of already completed user-dispatched run; no new workflow, editor or production runner mutation
SUPERSEDES: 20261106-item4-python-127-root-cause-scope-fixed.md
RUN: https://anthares.us/forgejo/anthares-admin/anthares-kwai-runner/actions/runs/2
FORGEJO_INTERNAL_RUN_ID: 588
FORGEJO_JOB_IDS: ci=589; cd=590
SOURCE_GITHUB_MERGE: 888f4180b905e36afb118364eb094003e08a7522
WORKFLOW_SOURCE_BLOB: 0e337f399371a3028898ce1df3def9e34db4712b
GOVERNANCE_MANIFEST_VERSION: 223433740e807a90
COST_ADDED: R$0
SOCIAL_PUBLICATIONS: 0

## Real terminal evidence
- Owner recovered existing scoped Hostinger runner process using its current private runner registration and config; user console returned `RUNNER_PROCESS_STARTED pid=85275`. The process PID is historic evidence, not a permanent liveness claim.
- Forgejo REST GET `/api/v1/repos/anthares-admin/anthares-kwai-runner/actions/runs/588` returned `status=success`; Forgejo job-state HTML bootstrap confirms both `ci` and `cd` have `status=success` and matching run #2.
- GET `/actions/runs/2/jobs/0/attempt/1/logs` HTTP200: at 2026-11-06T02:21:20.1507614Z `ANTHARES_FORGEJO_MAIN_IDENTITY=PASS sha=888f4180b905e36afb118364eb094003e08a7522`.
- Same CI log: at 02:21:20.195Z `ANTHARES_FORGEJO_PYTHON_VERSION=3.11.18`; all 3 quota-cancel tests finished `ok` and `ANTHARES_FORGEJO_MAIN_CI=PASS` at 02:21:20.3239573Z.
- GET `/actions/runs/2/jobs/1/attempt/1/logs` HTTP200: 2026-11-06T02:21:22.1722983Z `ANTHARES_FORGEJO_MAIN_CD=PASS sha=888f4180b905e36afb118364eb094003e08a7522`.
- The CD workflow writes the SHA-bound private receipt under `~/.anthares-forgejo/ci-main-cd/current.json` atomically, reads it back and asserts the SHA; the live `CD=PASS` marker confirms that code path completed on the Hostinger runner.
- Forgejo REST GET `/branches/main` returned exactly SHA `888f4180b905e36afb118364eb094003e08a7522`; user had already obtained `SYNC_PROVEN` for this SHA via existing read-only host receipt.
- The previous Forgejo run #1 (`567`) failed due to `python3.11: command not found`; PR #2125 corrected the interpreter selector and has merged. The successful run #2 demonstrates the fix on the actual host with Python 3.11.18.

## Acceptance and operational boundary
- Item #4: DONE / PRODUCTION_PROVEN for scoped, nonpublishing main repository Forgejo CI/CD.
- No retries or synthetic runs were issued during readback. The accepted run #2 was dispatched by the repo owner. No additional private credentials, runner registrations, subscriptions, publication workflows, or quota services were created.
- CI/CD is manual and verifies local code + SHA-only private attestation; it does not deploy any site or social media application.
- Hostinger runner process durability under reboot remains an independent operations concern, not a failing criterion for this one completed workflow run.
- GitLab mirror branch divergence is outside item #4; no cross-provider push performed.
