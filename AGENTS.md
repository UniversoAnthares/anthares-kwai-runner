# Shared test-hub protocol

Before changing or testing this project, read `test-hub/README.md` and the relevant files under `test-hub/findings/`.

Rules:
- Treat the hub as the shared source of truth across simultaneous chats/agents.
- Do not repeat a FAILED path unless the new test explicitly changes the recorded failure cause.
- Preserve PROVEN behavior unless a newer real test supersedes it.
- After every meaningful test, create a new append-only finding using the template in the hub.
- Never put credentials, secrets, cookies, tokens, or session payloads in the hub.
- A run that failed because the test harness itself was broken is not evidence that the tested hypothesis failed.


## Mandatory concurrency gate

Before EVERY state-changing action (code mutation, deploy, session/bootstrap change, queue mutation, publication, workflow trigger that mutates external state):

1. Refresh `test-hub/README.md`.
2. Read all new `test-hub/findings/` commits created since your last snapshot, not only files you already know.
3. Inspect currently RUNNING workflow runs and active deploys for the same causal area.
4. Create an append-only lease finding BEFORE the mutation:
   `test-hub/findings/YYYYMMDD-HHMM-lease-<area>-<short-purpose>.md`
   with:
   - `STATUS: RUNNING`
   - `AREA:`
   - `LEASE: <area>/<purpose>`
   - `BASELINE_COMMIT:`
   - `BASELINE_PROVEN:`
   - `FAILED_AVOIDED:`
   - `SUCCESS_SIGNAL:`
   - `FAILURE_SIGNAL:`
   - `TEST_VALIDITY:`
   - `EXPIRES_AT:` (maximum 30 minutes)
5. Re-read the repository HEAD immediately after creating the lease. If another active lease for the same area/purpose was created first, STOP mutating and observe only.
6. A lease is released only by a new append-only finding that references it and records PROVEN/FAILED/PARTIAL/SUPERSEDED evidence. Never edit/delete the lease.
7. Read-only diagnostics may run in parallel. Mutations in the same causal area MUST be serialized.
8. A test whose baseline commit/deploy changed after its lease was created is INVALID for the hypothesis; record it as harness/baseline invalid, not FAILED.
9. Before triggering a workflow, verify no causal RUNNING run already tests the same hypothesis. Do not create redundant matrices.
10. Never infer that a commit is deployed: verify the live deploy revision first.

Suggested causal areas: `tiktok-session`, `tiktok-publish`, `kwai-login`, `kwai-publish`, `kwai-live`, `cloudflare-control`, `queue`.

If append-only lease creation conflicts (409), refresh HEAD/findings and retry with a unique filename; do not proceed with the mutation until the lease is visible.
