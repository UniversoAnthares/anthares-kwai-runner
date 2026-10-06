# Lease: TikTok 15-environment low-memory browser replacement
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-06
LEASE_AREA: tiktok-publish
LEASE_EXPIRES: 2026-10-06T11:10:00Z
BASELINE_PROVEN: central TikTok session is valid; Render identity/upload auth is proven but 512Mi Render OOMs during real publish; GitHub auth acceptance is environment-dependent and replica 15 previously reached /upload.
FAILED_AVOIDED: no retry of unchanged Render 512Mi publisher; no repetition of identical 30-way GitHub contenders; no publication_started during this read-only matrix.
SUCCESS_SIGNAL: at least one materially distinct browser environment reaches authenticated TikTok /upload and confirms expected account.
FAILURE_SIGNAL: all 15 materially distinct environments redirect to login/challenge.
TEST_VALIDITY: each replica must fetch the same central session through protected OIDC and emit variant, auth-cookie count, final URL and account identity evidence. No irreversible publication occurs in this matrix.

Goal: select a proven free execution environment, then use exactly one serialized canary under the existing queue safety contract.
