# Kwai opaque local runtime installed
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-06
RUN: local authorized machine aic-lucas-pc
JOB: none
COMMIT: pending
SUPERSEDES: none

## Objective
Preserve the owner-authenticated isolated Kwai Studio browser as an opaque runtime without reading or exporting cookies, tokens, OTPs, or session storage.

## Result
PROVEN locally: isolated Chrome process using AntharesKwaiChrome remains running. A durable launcher was installed at %LOCALAPPDATA%\AntharesKwaiRuntime\launch.cmd and an autostart entry at the current user's Startup folder. The launcher reuses the isolated profile and opens studio.kwai.com. No credential material was read or copied.

## Evidence
RUNTIME_PROCESS=PROVEN
WRAPPER_INSTALLED=1
AUTOSTART_INSTALLED=1
RUNTIME_PROFILE_OPAQUE=1

## Consequence
The authenticated browser state now has a durable local runtime wrapper. This does not by itself prove cloud portability or a real post. kwai-login READY still requires non-secret identity/UI evidence from this opaque profile. Publication remains fenced under kwai-publish.
