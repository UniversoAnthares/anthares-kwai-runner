# CORTES own OAuth continuation
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-20
LEASE_AREA: cortes-drive-oauth
LEASE_OWNER: Codex/01a15c02
LEASE_EXPIRES: 2026-10-21T01:42:29Z
BASE_HEAD: 2e49451e3ce1a16728ab25b3848f6c432cad1679
SUPERSEDES: none
BASELINE_PROVEN: 20261020-cortes-bws-oauth-inventory-partial.md; 20261020-cortes-three-google-drives-aux-storage-preauth.md. Protected candidate has own client, no tokens for all three accounts. Legacy config preserved.
FAILED_AVOIDED: no shared OAuth, no failed SDK bootstrap retry, no copied browser sessions, no publication probes.
SUCCESS_SIGNAL: correct identity and own client per account, upload/recovery SHA256; unattended Secrets retrieval verified before enabling production.
FAILURE_SIGNAL: wrong account, unsupported scope, unavailable Automation bootstrap/write, hash mismatch or competing lease. Fail closed.
TEST_VALIDITY: listing, syntax or green jobs cannot prove backup. Real upload and recovery required per account. Unrelated local checkout changes preserved.
PEER_CHECK: GitLab 87307248 main findings read; prior BWS findings equal. No running GitLab pipelines or relevant GitHub runs/open PRs. New branch absent on peer. Main protected; no bypass, lease published on isolated branch and draft PR.
SCOPE: isolated own OAuth and backup code/docs, protected setup scripts; Secrets only with verified permission. No deletion of original media.
