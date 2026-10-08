# Alternative to Android emulator — 2026-10-08

Status: PARTIAL / RESEARCH ONLY. No production publishing claim. Existing Android runs must continue independently.

## Findings
- Android workflow repeatedly suffers from system-image cache path validation failures, boot overhead, and permission/onboarding screens.
- Candidate A: headless Chromium/Playwright on hosted GitHub Actions. No Android image, ADB, or emulator. First prove whether the Brazilian Kwai account can authenticate and expose a supported upload flow on kwai.com. Do not assume Kuaishou China interfaces are interchangeable with Kwai Brazil.
- Candidate B: official Kwai-compatible publishing partner/integration with account authorization, only if free and demonstrably supports the Brazilian account. Avoid Chinese Kuaishou Open Platform and cp.kuaishou.com (previously ruled out).
- Candidate C: persistent cloud Android only if it is genuinely free, remote, and independent of user's PC; no billing/card or trial-dependent service.

## Safe acceptance tests
1. Public, unauthenticated read-only browser probe: kwai.com supports login, but this alone does not establish web video publishing.
2. Authenticated browser proof requires the owner's approved session; never extract tokens or bypass account security.
3. Upload only an explicitly approved test video, verify post appears on the actual Brazilian Kwai account.
4. Compare elapsed time, reliability, and free quota with current Android.
5. No real posting and no workflow replacement until proof. Preserve ongoing Android tests and leases.

Official sources: https://www.kwai.com/support/video/how-do-i-post-a-video ; https://www.kwai.com/pt-BR/support . Kuaishou documentation at kuaishou.com describes a different platform and is not proof for Kwai Brazil.
