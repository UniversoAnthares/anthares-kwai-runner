# Auth-first acceptance: two timeout failures
STATUS: FAILED
AREA: kwai
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37947415466
JOB: 113877185379
COMMIT: be52eb792817262e50ab3ee0ea651f6e7349eee9
SUPERSEDES: 20261009-kwai-auth-first-two-runs-running.md

Both runs 37947415466 and 37947449351 failed at 12-minute Authentication first step timeout. First showed FAILURE_SIGNAL=KWAI_EMAIL_LOGIN_NOT_VISIBLE before KWAI_OWNER_INTERACTION_READY, then timeout. Second repeated KWAI_ONBOARDING_RIGHT_HEART_ATTEMPTS_EXHAUSTED before the same login-not-visible signal and late interaction-ready marker.

Cause: the step timeout begins before onboarding/navigation delivers a usable login surface. Prioritize actual usable login form, and begin interaction timeout only after readiness; separate preparation timeout. No identity or persistence proven.

Runs 37947977836 and 37948197230 still in progress at observation.