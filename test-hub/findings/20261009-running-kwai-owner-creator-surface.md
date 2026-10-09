# Exact owner verification from authenticated Creator Center/create surface
STATUS: RUNNING
AREA: kwai-existing-tab-owner-helper
DATE: 2026-10-09
RUN: none
JOB: none
COMMIT: f117c14fc0b226b6c5857f7c98183aa8b2a7d335
SUPERSEDES: 20261009-kwai-owner-menu-subtree-failed.md
BASELINE_PROVEN: signed-in UI is repeatedly proven and create_probe has operational_create_surface=true with no login gate, while public profile/menu/account-row/hydration strategies did not bind the exact handle.
FAILED_AVOIDED: do not repeat menu-only evidence. Use a distinct authenticated first-party creator/create context. Never select media or click Publish/Post.
SUCCESS_SIGNAL: after safe navigation to Creator Center or activation of Create/Upload, the resulting authenticated surface contains exact @universo.anthares identity evidence in visible/profile-link/contextual React state and live owner_probe returns identity_verified=true.
FAILURE_SIGNAL: creator/create surfaces are reachable but no exact-handle binding exists, or a login gate appears.
TEST_VALIDITY: QA validates syntax/security only; live Codespaces owner_probe is required. No cookies/storage/tokens/raw page text/screenshots are exported.
