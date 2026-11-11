# AOI #7 — Hostinger hPanel authenticated Forgejo keepalive deployment
STATUS: RUNNING
AREA: architecture/forgejo-daemon-hostinger-live
DATE_UTC: 2026-11-11
OWNER: chatgpt-hpanel-forgejo-20261111
LEASE: ops/forgejo-hpanel-safe-cron-20261111
BASE_GITHUB_SHA: 69c61f72ac99f238bdad41922af67fa9c65be646
SCRIPT_GITHUB_BLOB_SHA: 966e539447a814da72f8db0c8a682cef1603fe0b
SUPERSEDES: 20261110-forgejo-keepalive-source-fixed-partial.md
GOVERNANCE_SHA: 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
PREVIOUS_LEASE: closed, no running Forgejo keepalive lease observed
PROVIDER_PEER: GitLab 87307248 keepalive script is historical, not updated.
BASELINE_PROVEN: Owner authenticated Hostinger hPanel for anthares.us through dedicated AntharesTinyFish Chrome profile. Cron Jobs has two Forgejo mirror tasks (17 hourly AVS; 0,30 half-hour Git). Hostinger all-files GUI lists ~/.anthares-forgejo/ with binary, custom config, socket and log; 129 entries fully loaded, forgejo_keepalive.sh absent. Corrected source exists in canonical GitHub main, previously tested via seven local synthetic scenarios and merged #2337. Hostinger ARA device itself is read-only; operations below are via owner's independently authenticated hPanel.
FAILED_AVOIDED: Do not alter any existing mirror job, SSH account, passwords, Git refs, secrets, WordPress, Kwai, TikTok, other browsers or agent windows. Respect prior blocked SSH/HTTPS origin verification; do not attempt it via alternative controller. Do not add duplicate cron; do not overwrite an existing file.
SUCCESS_SIGNAL: File created in existing private Hostinger directory with content identical to GitHub source, one new five-minute cron calling /bin/bash path, cron output readback confirms health or recovered process. Source file and existing cron jobs preserved.
FAILURE_SIGNAL: Could not inspect the file manager editor, write verification fails, cron duplicate found, service restart fails, permission denied, security control rejects action, or no independent readback.
TEST_VALIDITY: Hostinger GUI explicit file-list and cron readback; no publication jobs; installation is not daemon healthy until run+health attested.
ADDED_COST: zero
