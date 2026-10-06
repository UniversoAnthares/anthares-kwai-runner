# Kwai Studio opaque runtime — main profile authenticated, isolated profile not authenticated
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-06
RUN: local authorized machine aic-lucas-pc
JOB: none
COMMIT: pending
SUPERSEDES: 20261006-1836-lease-kwai-opaque-runtime-final.md

## Objective
Verify the owner-authenticated Kwai Studio surface without reading or exporting session credentials.

## Result
The isolated AntharesKwaiChrome profile opened Studio at the login/challenge surface, so it is not READY and must not be promoted. The existing main Chrome profile opened studio.kwai.com/live/list directly into an authenticated Studio page showing the owner's existing traffic/live records and account avatar. This is valid non-secret UI evidence of an authenticated Kwai Studio web session in the main profile.

## Evidence decisiva
AI Commander screenshot at machine time 2026-10-06T18:38:26Z showed, simultaneously, isolated profile on login/challenge and main Chrome on authenticated Studio list. No cookies, tokens, Local Storage, Session Storage or IndexedDB were read or exported.

## Consequence
Do not claim the isolated profile READY. Preserve the main Chrome Studio session as an opaque authenticated web runtime. The existing canonical kwai_publish_video.py remains Android-app based, so Studio web authentication does not by itself prove Android publisher readiness or a real post. A web publisher must be treated as a distinct causal route and still obey one-at-a-time fencing and independent verification.
