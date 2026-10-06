# Anthares Android Agent protocol

The Agent surrounds the official Kwai application; it does not implement or emulate Kwai server APIs.

## State contract
BOOT -> KWAI_NOT_RUNNING -> KWAI_STARTING -> PERMISSION/ONBOARDING_INTEREST/START_GATE -> MAIN -> PROFILE -> LOGIN_REQUIRED -> AUTHENTICATING -> AUTHENTICATED -> READY.

Error/holding states: LAUNCHER_ANR, KWAI_CRASH, NETWORK_UNAVAILABLE, RESOURCE_LOADING, UNKNOWN_UI, AUTH_CHALLENGE, SESSION_EXPIRED.

Every future transition must define detector, semantic action, timeout, recovery, telemetry and evidence. READY requires positive account identity evidence; MAIN/Profile/feed alone never imply authentication.

## UI policy
Prefer resource-id, AccessibilityNodeInfo text/contentDescription and hierarchy. Coordinates are fallback diagnostics only. ll_profile is a known semantic anchor from the proven FSM.

## Telemetry
Log state changes as AntharesAgent STATE=<state> and actions as AntharesAgent ACTION=<action>. Never log passwords, cookies, tokens, session payloads or secret values.

## Publication boundary
The Agent exposes state/navigation primitives to the kwai-publish layer. Publication remains blocked until READY and positive identity verification.
