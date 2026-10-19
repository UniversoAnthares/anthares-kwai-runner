# Lease renewal — independent SSH automation
STATUS: RUNNING
AREA: ara-ssh-recovery
DATE: 2026-10-19
BASE_HEAD: ab47afb6656d034031bcf0abde16c0e0546bc1b7
LEASE_OWNER: codex-ssh-recovery-20261019
LEASE_EXPIRES_UTC: 2026-10-19T12:48:00Z
SUPERSEDES: 20261019-1152-lease-ara-ssh-recovery.md

BASELINE_PROVEN: GitHub-hosted run 39249878095 attempt 3 emitted SSH_INDEPENDENT_PROVEN=1 at 12:16:15Z. JSON validates hostname DESKTOP-FTDK0HP, administrator=true, canonical_tasks_valid=true, primary_count=1, reserve_count=0, action_performed=false. GitHub encrypted environment secret was provisioned only after explicit owner approval. Tailscale Free account, exact OIDC issuer/subject IDs/environment, restricted tag policy, Windows interface-scoped firewall and private listener verified.
FAILED_AVOIDED: Official Action already supplies accept-routes; conflicting flag was removed and routes disabled with tailscale set before SSH. Tailscale credential edit did not persist subject changes; replacement was created with the exact immutable-ID subject from the issuer, preserving the same scopes/tag. No broad subject wildcard was used. Disabled legacy watchdog remains disabled. Its lastgood arbiter differs (5400s) from live (90s), so it must not be re-enabled/restored blindly.
SUCCESS_SIGNAL: New monitor and conservative quota gate pass tests; real SSH probe passes at the final source; reviewed deployment preserves local tasks/publisher state. Automatic healthy no-op and monitor dispatch may be tested, but a real repaired failure is NOT_TESTED unless a natural failure occurs.
FAILURE_SIGNAL: Any attempted duplicate authority, missing budget evidence, unauthorized branch or invalid pin must block action.
TEST_VALIDITY: No agent stop, Windows reboot or publication interruption. Keep Neon and existing local recovery architecture intact. Activation occurs only after final-source hosted validation.
