# Five independent safety probes — PROVEN
STATUS: PROVEN
AREA: qa / kwai-heartbeat / cloudflare-auth
DATE: 2026-10-05
RUN: 37402452239
JOBS: 112072420959 ; 112072421161 ; 112072421206 ; 112072421229 ; 112072421269
COMMIT: 3789c79858a84545954225cc22236e7b34dac8de
SUPERSEDES: test-hub/findings/20261005-lease-five-independent-safety-probes.md

## Five independent probes
1. first-renew: PROVEN. Heartbeat performs fenced renew immediately before child launch. Initial matrix exposed the previous delayed-first-renew gap; commit 9d09b2130ebefb443367a61b3c1aed0e4b320b6f fixed it causally.
2. descendant-kill: PROVEN for tested shell-child/grandchild scenario. Forced periodic renew loss returns 49 and descendant is not alive afterward.
3. invalid-config: PROVEN. interval <15 returns 46; TTL <= interval returns 47.
4. exit-propagation: PROVEN. Normal child exit 23 is preserved as 23.
5. control auth boundary: PROVEN. Public health remains control v16 and a new, non-allowlisted OIDC workflow is rejected rather than gaining queue-self-test mutation rights.

## Earlier attempts
Run 37402210971 intentionally exposed first-renew failure; control-v16 case was invalid because the first harness omitted id-token permission.
Run 37402328258 proved four heartbeat cases after the fix; the fifth demonstrated exact workflow allowlisting. The final matrix reframed that as the intended adversarial auth assertion instead of weakening production authorization.

## Safety
No Kwai login/Android mutation, media publication, anonymous YouTube extraction, or Cloudflare deployment occurred.
