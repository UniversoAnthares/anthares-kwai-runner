# AOI #7 — recuperação do daemon Forgejo existente
STATUS: RUNNING
AREA: forgejo-daemon-hostinger / git-mirror-avs
OWNER: chatgpt-aoi7-hostinger-20261109-0214
DATE_UTC: 2026-11-09T02:14:00Z
EXPIRES_UTC: 2026-11-09T02:44:00Z
FIXED_ITEMS: [7]
SOURCE: existing Hostinger account; no new infrastructure
GOVERNANCE_VERSION: 223433740e807a90
BASE_GITHUB_SHA: 6b64b9ba9f6ad787139ddf27f98d2627b75b64f8
BASE_HOSTINGER_AVS_SCRIPT_SHA256: 44742047287d3cf6049c60ea33b14126b96ca7d0c7b2031a8c0281ea48fc5167

## BASELINE_PROVEN
At 02:00:20Z primary Hostinger mirror had 15 indexed repos, zero failures, and verified/fast-forward refs for regular repos; GitLab extra mirror had zero failures at 02:00:22Z. Independent AVS mirror status was failed (01:17:01Z). At 02:08Z authenticated GitHub AVS source SHA was 9d07eee4a5c991186a6cb646bde6ecf168e500b9; HTTPS Forgejo destination returned HTTP 502, with private bare git objects preserved. No Forgejo daemon process or socket listener observed.

## FAILED_AVOIDED
Do not edit unrelated media, publishing, secrets, Windows storage, or other workers. No provider 403 bypass; HTTPS 502 is a technical service outage. Do not use --force or --prune. Avoid executing keepalive.sh's unrelated 9router hook. Do not operate unless host lock is free, no other recovery owner is active, and target file SHAs match.

## SUCCESS_SIGNAL
The existing Forgejo binary is restored with original configuration and supervision; private authenticated HTTPS API responds; AVS mirror refs advance via authenticated non-destructive route; all source head and tag refs read back; no duplicated instance, new cost, or publication.

## FAILURE_SIGNAL
Daemon startup fails, source identity denial, target authorization denial, lock conflict, drift in current script, destination refs diverged, or CI/publisher interference. Preserve state and require independent reconciliation.

## TEST_VALIDITY
One authenticated HTTP readback and one nonpublishing mirror acceptance, only if permitted by gates. A proxy error or unassigned job cannot be marked successful. 