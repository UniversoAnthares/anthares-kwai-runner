# AOI #3 — live authenticated inventory lease
STATUS: RUNNING
AREA: x-ledger-inventory/live-readback
OWNER: chatgpt-aoi3-20261105
BASE_HEAD: 640676473cc03bd638640cfcc1680857f3e3c47c
DATE_UTC: 2026-11-05T03:04:33.543Z
EXPIRES_UTC: 2026-11-05T03:34:33.543Z
ITEMS: [3]
GOVERNANCE_SHA: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
BASELINE: 2026-10-29 run 40913350160 proved 9 CONFIRMED plus #1002 NOT_FOUND; issue #1002 still OPEN, zero comments, last updated 2026-10-22. Neon 9 confirmed rows. Workflow x-legacy-ledger-inventory.yml disabled_manually.
SCOPE: one manual READ-ONLY GH-hosted inventory, restore disabled_manually, reconcile source only; no posts, no SQL write, no queue claim.
PROVEN_SIGNAL: current old ledger all 10 matches historical identities and no uncertain; issue zero original comments; pin exact proof for migration.
FAIL_SIGNAL: missing secret, old state changed, SHA drift, job failed, unknown/started => quarantine #1002; no retry.
TEST_VALIDITY: actual authenticated /x/post-status, GitHub issue comments; no social post or browser execution.
