# Lease — item 11 Instagram Graph credential classification
STATUS: RUNNING
AREA: architecture/instagram-graph-auth
DATE: 2026-10-30
RUN: none
JOB: none
COMMIT: d3566514838799a3a0cfb84eace74bc508bd53ba
SUPERSEDES: none

BASELINE_PROVEN: hosted Graph preflight had INSTAGRAM_TOKEN_CONFIG_PRESENT=True and INSTAGRAM_GRAPH_PROFILE_CHECK=4 on Linux and Windows. Direct cloud run 41029247861 had both graph.instagram.com and graph.facebook.com rejected with only InstagramAPIError class. Buffer primary hosted run 41036577042 successfully scheduled six and reconciled four existing items; Buffer status alone does not prove direct Graph token valid. WordPress authenticated P0 QA readback is already proven 41056710386.
FAILED_AVOIDED: no same preflight retry without causal diagnostic, no token output, no Graph POST, no publishing, no secret rotation without verified account. Preserve live Buffer and Neon CAS.
SUCCESS_SIGNAL: trusted hosted PR test displays sanitized provider HTTP, Meta error code/subcode for existing token family and any existing alternative configured secret family; no raw message or tokens. Exact account identity must match before declaring official Graph auth valid.
FAILURE_SIGNAL: credential absent, unauthorized/expired token, upstream API failure, target mismatch, test connection error.
TEST_VALIDITY: read-only GET with bounded response on known Graph hosts; diagnostic alone does not establish publishing.
LEASE_SCOPE: .github/workflows/cortes-instagram-graph-auth-preflight.yml (and this finding), expires after 30 minutes.
