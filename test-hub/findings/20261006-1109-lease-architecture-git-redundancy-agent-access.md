# Lease — Git redundancy final agent access
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## BASELINE_PROVEN
Forgejo public endpoint is live at anthares.us/forgejo and external git ls-remote succeeds. Finding 20261006-1058 records daemon-liveness caveat and GitLab OAuth gate.

## FAILED_AVOIDED
Do not retry GitLab SSH without a new credential. Do not use Cloudflare Quick Tunnel. Do not claim Forgejo watchdog PROVEN. Do not expose existing Forgejo server token.

## SUCCESS_SIGNAL
Dedicated least-privilege Forgejo agent credential performs API read plus controlled branch/commit and cleanup; GitLab OAuth status is determined without exposing tokens.

## FAILURE_SIGNAL
Forgejo dedicated credential cannot be generated/stored safely or public API path cannot authenticate; GitLab remains at explicit OAuth consent.

## TEST_VALIDITY
Re-read HEAD after lease. Abort mutation if an earlier active architecture lease for Git redundancy exists.

## Lease
OWNER: chatgpt-git-provider-redundancy
EXPIRES: 2026-10-06T15:38:00Z
SCOPE: Forgejo agent credential/MCP access and GitLab OAuth status only.
