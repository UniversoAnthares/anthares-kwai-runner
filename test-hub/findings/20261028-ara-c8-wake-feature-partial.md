# ARA C8 external wake — source gate
STATUS: PARTIAL
AREA: queue / ara-external-wake-C8
DATE: 2026-10-28
SUPERSEDES: test-hub/findings/20261028-ara-c8-wake-feature-lease.md
BASELINE_PROVEN: production C8 uses 2-second polling, 60-second heartbeat, with independent issue-queue fallback and canonical Vercel/Neon leases.
RESULT: optional feature code in main.go was rolled back after the external wake module write was explicitly denied by provider security. The branch main.go blob is restored exactly to the original 13172ffe3dac06dddd92874020fa489ed02bdffe. No production deployment, Windows process, queue, token or database was changed.
BLOCKER: code mutation for external signaling denied by integration security policy. No alternative channel was used to replay the refused write.
ACCESS: Anthares Remote capability succeeded but two read-only remote_exec calls aborted; WinRemote read-only Shell failed internally; MeshCentral device list timed out.
ROLLBACK: source restoration commit 06635986d4fabf2dc50cb9e5751451d8392b0fb2. Canonical C8 executable remains unchanged.
TEST_VALIDITY: no new code was deployed, so no claim of integration test or idle-compute savings.
OWNER: ChatGPT GPT-6, lease closed.
