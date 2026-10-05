# Exported Kwai UriRouterActivity declares direct internal login routes
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388030409
JOB: 112026171392
COMMIT: d9a144b23fbca831e4b382aa710549b68d9af77a
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-1959-qa-kwai-exported-auth-runtime-no-login.md; the authorization/partner exported URI set was runtime-negative.
FAILED_AVOIDED: do not repeat ikwai://authorization, kwai://authorization, ikwaipartner://auth or com.kwai.video://auth. This finding introduces a distinct Manifest-declared route and does not launch it while another kwai-login lease is active.
SUCCESS_SIGNAL: valid Manifest exposes an exported router with explicit VIEW+BROWSABLE+DEFAULT route whose host is login/loginchannel.
FAILURE_SIGNAL: route is absent/non-exported or only inferred from strings.
TEST_VALIDITY: static evidence comes from the already-valid aapt artifact of run 37388030409; runtime behavior remains NOT_TESTED.

## Resultado
`com.kscorp.oversea.platform.router.ui.UriRouterActivity` is exported and its valid Manifest contains an intent-filter for VIEW + DEFAULT + BROWSABLE with `android:scheme=ikwai` and hosts `login` and `loginchannel`. These are distinct from the exported authorization URIs already tested and failed. The route is therefore a new causal candidate, not a repetition of the failed authorization gateway experiment.

## Consequência
The active kwai-login agent should incorporate this contract before opening another route matrix. A future single probe may invoke `ikwai://login` first and observe whether the internal LoginActivity/EditText surface appears. It must preserve the proven FSM baseline and classify harness/precondition failures as INVALID. Do not test guessed credentials or query parameters until the route itself is runtime-proven.
