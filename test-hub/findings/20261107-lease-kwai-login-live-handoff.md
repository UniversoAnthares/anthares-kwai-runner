# Kwai mobile authentication handoff
STATUS: RUNNING
AREA: kwai-login
OWNER: codex-kwai-mobile-auth-20261107
LEASE_UNTIL: 2026-11-08T02:13:49Z
HEAD_BASELINE: 295bd94b3c89e5493e3860eb0bf4b0ba64831fd4
WORKFLOW_BLOB: bc50de3517c4292656d0b442c1fd8ced7183930a
GOVERNANCE_MANIFEST: 84905aefc5589d17
BASELINE_PROVEN: Hosted run 42400029536 verified the private tunnel and reached the interactive wait, then expired. Publish was skipped. The URL was emitted only to the job summary.
FAILED_AVOIDED: No repeated run without a live handoff, no credentials in the status, no publication, no queue access and no local Android executor.
SUCCESS_SIGNAL: Live protected handoff, exact Android UI identity, encrypted vault acknowledgement, and two independent fresh Android restores.
FAILURE_SIGNAL: Handoff is unavailable while the job is active, the identity or vault save fails, or either fresh restore fails.
TEST_VALIDITY: Dispatch mobile_auth on the vault-authorized main ref. Each restore must pull independently and verify the official app profile on a separate hosted runner.
PEER_CHECK: GitLab connector returned HTTP 403; no mirror write or failover attempted.
