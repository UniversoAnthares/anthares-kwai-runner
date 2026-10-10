# Lease: fail-closed queue publisher Cloudflare version preflight
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-10
OWNER: chatgpt-autonomous-queue-preflight
LEASE_UNTIL: 2026-10-10T15:07:20.332Z
HEAD_BASELINE: b60e357cf1a3f6ca3dd251d9d8559990639c9647
RESOURCES: .github/workflows/kwai-queue-publisher.yml
BASELINE_PROVEN: current queue publisher already requires deployed control version 2026-10-05-queue-fencing-v16 via kwai_claim_job.sh and kwai_queue_state.sh. Bridge recovery run 38056900085 independently observed deployed /health version 2026-10-05-no-pc-confirmation-v12 at 2026-10-10T13:48:41Z. Current scheduled publisher run 38060359638 was in progress when this lease was prepared.
FAILED_AVOIDED: do not repeat Android boot solely to discover a control version mismatch; no publication, no credentials, no browser, no PC executor, no change to queue lease or authentication logic. Independent static preflight layer only, no competing publish experiment.
SUCCESS_SIGNAL: workflow syntax validated and preflight gates Android publish job on exact deployed v16, persistent_state, queue_bound and pc_fallback=false; blocked control must skip publisher.
FAILURE_SIGNAL: invalid workflow syntax, wrong job dependencies, or publisher starts while control version mismatches.
TEST_VALIDITY: static validation is independent of current in-progress publisher; no real publication attempted. A successful workflow without actual publication is never publication proof.
SUPERSEDES: none
