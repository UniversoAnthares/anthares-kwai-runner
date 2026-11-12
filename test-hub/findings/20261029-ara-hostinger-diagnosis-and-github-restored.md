# ARA autonomous Hostinger diagnosis and owner-directed GitHub restoration
STATUS: PROVEN
AREA: anthares-remote/windows-identity-routing
DATE: 2026-10-29
RUN: none
JOB: ARA f11e3bc3c7265b66e7f767b0744f7afb
COMMIT: this branch
SUPERSEDES: 20261029-ara-context-router-final-acceptance.md

BASELINE_PROVEN: Existing owner SSH reaches Hostinger; canonical SYSTEM ARA is unchanged. Initial PowerShell broker showed connection/cleanup stalls and is superseded by the framed Python broker.
FAILED_AVOIDED: No second queue consumer, copied credential, forced owner Work handoff, credential revocation, social publication or retry of denied deployment/package changes.
SUCCESS_SIGNAL: Real SYSTEM ARA -> owner -> Hostinger returns private listener metadata, credential_read=false, completed, exit 0.
FAILURE_SIGNAL: Wrong identity, unsafe file ownership/access, secret read, duplicate execution or surviving owned server.
TEST_VALIDITY: Actual authenticated metadata and identity calls only; no package activation or production job.

## Effective changes and evidence
- Owner explicitly requested undoing the GitHub route block. No token was revoked or changed; private config github_enabled=true. Current GitHub identity UniversoAnthares was proved again under the registered owner SID.
- Runtime backend context_router.py SHA256 491cfb46dde63015d1dcb5264ab56913b08dbb05129f6ecbdaec22ae6a28fee1; compatibility adapter SHA256 a09d16ae8d3a9e7e7afde2aad41ddea51e553cfe41af83a2aad89ce4e441bcca.
- ARA job f11e3bc3c7265b66e7f767b0744f7afb, request a3ee104fe2034a95a4bfa10492d33abd: COMPLETED, exit 0, timed_out=false, owner executor, Hostinger SSH metadata exists=true, regular_file=true, symlink=false, nonempty=true, owner_matches_executor=true, group_or_other_access=false, credential_read=false.
- GitHub request d06040580cbd47c898f6cb8e6be9127e: COMPLETED, expected identity. Cloudflare request 0b60a3d180e34740877e8e683c08d552: COMPLETED, configured account verified.
- Hostinger read-token request bd4cc09a6b6e42e29afb8a3af7abc096 rejected as unregistered; GitHub auth token request 2a870443d8cd4054ae1e9f7f768a20e0 rejected before credential access. Reusing the real Hostinger request ID was rejected after process restart. Four synthetic redaction fixtures passed.
- Task remains owner Interactive/Limited, starts automatically per request and returns Ready/exit 0. Named-pipe ACL, server SID validation and per-request Windows Job Object protect context and process lifecycle.
- Central local governance 84905aefc5589d17 updated and synchronized to 210 repositories; eight stale non-repository entries account for 32 audit failures and were not altered.

## Boundaries
The Hostinger file-check handoff to Work was unnecessary. File metadata diagnosis is now callable through ARA alone. This does not authorize reading/exporting the credential or retrying Windows code replacement/GitHub branch writes explicitly denied in another task. No event-driven C8 deployment was performed or claimed. Interrupted requests retain their IDs for reconciliation; do not replay unknown effects. The earlier technical-output credential exposure remains in the historical finding, without its value; the owner's later instruction restored the route without revocation.
