# Lease — Item 5, verificar recibos Buffer históricos sem ID remoto
STATUS: RUNNING
AREA: cortes-item5-buffer-history-readback
DATE_UTC: 2026-11-11
OWNER: chatgpt-item5-legacy-buffer-readback
BASE_HEAD: 2156c6cd7550f5a573bce316dd863e9086ea1d4a
BASELINE_PROVEN: 13 uncertain records without remote_id on Pinterest (7), LinkedIn company (2), Instagram (4). Exact media URL fingerprint md5 truncated to 24 hex available from Neon. Buffer read API supports posts list with source media and public link; existing LinkedIn cloud worker holds scoped Bitwarden Buffer access.
FAILED_AVOIDED: no direct SQL mutation, no tests, no publication, no resend, no local media, no credentials in source or logs.
SUCCESS_SIGNAL: authenticated Buffer readback finds unique exact media source per previously orphaned item with permitted platform/channel status and external public permalink. Absence does not prove no public post.
FAILURE_SIGNAL: provider API rejection, rate limit, wrong channel, incomplete pagination, duplicate asset matches; preserve original states.
TEST_VALIDITY: productive read-only reconciliation of existing user posts; no synthetic tests.
LEASE_STATUS: OPEN
