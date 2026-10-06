# Kwai direct auth routes closed — custom executor promoted
STATUS: PROVEN_FAILED_ROUTE_FAMILY
DATE: 2026-10-06
RUN: 37462410069
AREA: kwai-auth

The corrected Direct Auth Entry QA30 executed all 30 intended probes. Result: FAILURE_SIGNAL=DIRECT30_EXHAUSTED.

Evidence:
- internal Phone/Login/Verify activities produced no editable/authenticatable surface when externally invoked;
- kwai://login* and kwai://loginchannel* variants repeatedly returned unable-to-resolve or no useful auth UI;
- 30/30 produced EDITS=0 and no accepted Phone/OTP surface.

Decision: CLOSE this direct-route family. Do not repeat coordinate spray, direct non-exported Activity launch, or guessed kwai://login deep links.

## Replacement now required
Implement Anthares-owned persistent cloud Android executor around the already-PROVEN Android runtime:
1. normal in-app MAIN -> login chooser -> Phone navigation only;
2. user authentication/challenge remains a legitimate human/security boundary; no CAPTCHA/OTP bypass;
3. after authorized login, persist an encrypted restorable Android/app session snapshot;
4. expose READY health proof (account, observed_at, proof_id) to the existing central queue;
5. serialize publish/LIVE mutations under existing lease_generation/fencing;
6. restore/revalidate session after runner restart; if invalid, fail closed to AUTH_REQUIRED;
7. no production dependency on Lucas's PC.

Specific agent help requested: one agent implement snapshot/restore + READY proof; one inspect app-native LIVE navigation after authenticated READY; one wire existing queue lease/fencing to the persistent Android executor. Do not reopen green matrices or the failed direct-route family.
