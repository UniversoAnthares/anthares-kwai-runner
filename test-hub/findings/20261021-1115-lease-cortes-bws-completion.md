# CORTES Secrets completion resume
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-21
LEASE_AREA: cortes-drive-oauth
LEASE_OWNER: Codex/01a15c02
LEASE_EXPIRES: 2026-10-21T11:44:49Z
BASE_HEAD: abb65d82123a2beee09898a788045381df5abace
SUPERSEDES: test-hub/findings/20261021-0228-lease-cortes-bws-runtime.md
BASELINE_PROVEN: All three OAuth identities and SHA256 upload/recovery passed; candidate and parent ACL restricted. Existing Automation project/machine write access inspected. No temporary machine token was created before prior session paused; receiver expired without a credential. User now requests continuation, vault session available.
FAILED_AVOIDED: do not repeat failed historical SDK bootstrap; validate complete newly issued token against official bws CLI and exact Automation scope before SDK writes. No secret arguments/logs, no browser session copying, no source deletions.
SUCCESS_SIGNAL: vault bundle write/readback; readonly CORTES machine credential; unattended hydrate and recovery; temporary write token revoked. Fail closed if any gate missing.
FAILURE_SIGNAL: scope/identity mismatch, invalid bootstrap, integrity failure or conflicting lease.
TEST_VALIDITY: Google success alone not Secrets runtime proof. Only real readback/hashes count.
PEER_CHECK: peer new finding absent, destination branch/tree and current hub policy/runs reread. New isolated source files absent on peer; no destructive mirroring.
