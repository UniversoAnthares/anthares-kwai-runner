# Ajuda específica — substituir rotas esgotadas e fechar gates finais
STATUS: OPEN
DATE: 2026-10-06
AREA: final-red-gates

CLOSED / DO NOT RETEST:
- TikTok v15 reconciliation 30-way: PROVEN ABSENT, run 37459757627.
- Kwai APK auth component discovery: PROVEN, run 37460279417.
- Kwai Phone surface QA30, Android runtime baseline, SHA dedupe/control safety, public HLS.

FAILED / AVOID:
- Kwai direct/exported auth entry matrices 37461362773, 37461375443, 37461413020, 37461899599, 37462410069. Direct component starts are blocked/not externally reachable and URI variants do not resolve; do not repeat this family without a causal APK/version/export change.
- TikTok environment replacement matrix 37461651712 hit protected session-state 401; changing runner/locale/viewport is not a causal fix.
- Do not repeat coordinate spray or bare ikwai://login.

HELP REQUESTED:
1. Inspect the currently deploying Cloudflare revision/run 37463135822 and identify the narrow OIDC identity/source needed by the serialized TikTok publisher. Patch allowlist only if exact workflow identity is missing; no wildcard.
2. Design/implement Anthares-owned persistent cloud Android session bootstrap for Kwai: encrypted state/snapshot artifact, READY health proof, restore on fresh executor, queue lease/fencing. This replaces direct-Activity/coordinate experiments; OTP/challenge remains human-authorized.
3. For LIVE, reuse that authenticated Android bootstrap and test only legitimate app-native LIVE/session handoff. HLS is already closed. Do not bypass Studio CAPTCHA/challenge.
4. Return exact run/commit/finding and SUCCESS_SIGNAL/FAILURE_SIGNAL. Respect active leases before mutation.

SUCCESS_SIGNAL: TikTok serialized publisher reaches its next real transition after authorized session retrieval; Kwai custom bootstrap restores a READY-capable authenticated state without PC.
FAILURE_SIGNAL: proposal depends on local PC, bypasses challenge, or repeats an exhausted route.
TEST_VALIDITY: irreversible actions remain serialized; 30-way is only for reversible diagnostics.