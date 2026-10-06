# Lease: multi-executor CI foundation
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-05
EXPIRES: 2026-10-05T23:05:00-04:00
OBJECTIVE: add provider-neutral test/log hub plus CircleCI, GitLab CI and Bitrise configurations without changing Kwai session state.
BASELINE_PROVEN: GitHub is canonical source/hub; Android Agent APK build is PROVEN; current GitHub hosted runs are capacity-blocked/queued.
FAILED_AVOIDED: no repeated deep-link/login probes; no dependence on local PC; no assumption that a provider account is already connected.
SUCCESS_SIGNAL: provider configs and per-provider append-only log directories exist in canonical repo and validate structurally; external execution starts only after provider authorization.
FAILURE_SIGNAL: provider config cannot express the shared smoke/runtime contract or would require PC/local executor.
TEST_VALIDITY: repository changes alone prove integration readiness, not provider execution; a provider is ACTIVE only after its own pipeline emits PROVIDER_HUB_OK and runtime success marker.
