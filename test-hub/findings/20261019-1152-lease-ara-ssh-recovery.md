# Lease — independent SSH recovery
STATUS: RUNNING
AREA: ara-ssh-recovery
DATE: 2026-10-19
BASE_HEAD: 97798a3332d4f151b458b0ab3085dee8cc9ed2a9
LEASE_OWNER: codex-ssh-recovery-20261019
LEASE_EXPIRES_UTC: 2026-10-19T12:22:00Z
BRANCH: codex/ssh-recovery-20261019
SUPERSEDES: none

BASELINE_PROVEN: Local OpenSSH public-key login and elevated administrative token; Tailscale Windows online at 100.89.147.45. Existing SYSTEM watchdog and cold-reserve arbiter remain canonical. See 20261015-ara-c8-hardened-f6-complete.md, 20261015-ara-phase4-homologation.md and 20261016-1902-system-authority-failover-final-policy.md.
FAILED_AVOIDED: Do not expose localhost SSH before private client identity and restrictive firewall/ACL exist. Do not treat queue transport as independent of the Windows agent. No Render, reboot, stopped agents, publication probes or second recovery authority.
SUCCESS_SIGNAL: Standard GitHub-hosted Linux runner makes a real key-authenticated SSH request across Tailscale, validates pinned host key, returns DESKTOP-FTDK0HP and privileged identity. Separate synthetic policy tests prove 90-second grace, stale evidence rejection, cooldown and no competing recovery. Actual repair remains NOT_TESTED unless an authentic failure occurs naturally.
FAILURE_SIGNAL: Missing trust credential, inaccessible runner, invalid host key, denied SSH, duplicate authority or unverified policy fails closed.
TEST_VALIDITY: Runner ID, workflow commit and explicit SSH_INDEPENDENT_PROVEN marker required; job success alone is insufficient. Existing agents must remain running throughout. Existing 90-minute reserve policy in historical finding differs from live arbiter's 90-second value; neither is modified by this change. SSH only wakes the existing canonical watchdog when it is absent; it never starts/stops agents itself.
PEER_CHECK: GitLab duo-main lacks the new SSH entry file; main ref is absent. No reconciliation/mirror attempted. New GitHub files only.
