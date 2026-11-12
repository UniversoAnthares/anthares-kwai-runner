# CORTES Secrets runtime continuation
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-20
LEASE_AREA: cortes-drive-oauth
LEASE_OWNER: Codex/01a15c02
LEASE_EXPIRES: 2026-10-21T02:58:24Z
BASE_HEAD: e0b7184af5b83a310ad4dd4e91685e3bfe47b920
SUPERSEDES: test-hub/findings/20261021-0153-lease-cortes-drive-owner-resume.md
BASELINE_PROVEN: All three correct Google accounts passed own-client drive.file real 64KiB upload/recovery SHA256; Profile9 rerun after root assignment passed. Profile3 job94beb7770ac64541 PASS; Profile2 jobd2d14d36fffafca8 PASS. Own-client API initially disabled (403 SERVICE_DISABLED); Drive API enabled in anthares-login, no YouTube/consent scope changes. Parent/config ACL hardened after rclone atomic replacement inherited broad ProgramData ACL.
FAILED_AVOIDED: no old failed SDK bootstrap reuse. Newly provisioned full machine token must pass official CLI project access check before SDK write; SDK no persisted state, no secret CLI arguments or output. No main/checkouts reset or publication probes.
SUCCESS_SIGNAL: encrypted Bitwarden bundle readback, readonly exact-secret machine access and unattended retrieval plus real recovery through hydrated config; temp write credential revoked at completion.
FAILURE_SIGNAL: account/root/permissions mismatch, credential unavailable, hash mismatch, competing lease or inability to revoke temporary access. Fail closed.
TEST_VALIDITY: API enable and GUI consent alone not operational backup; actual hashes recorded separately. No production activation before Secrets runtime verification.
PEER_CHECK: peer new finding absent; GitHub branch HEAD/tree reread. No conflicting Drive chain in current findings/runs. Previous lease expired; fresh scoped continuation.
