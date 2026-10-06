# Promotion gate + workflow boundary QA — PROVEN
STATUS: PROVEN
AREA: control-integration
DATE: 2026-10-06
RUNS: 37405770727; 37405774727
RESULT: 10/10

Promotion gate 5/5:
- valid canonical contract accepted.
- zero generation rejected.
- reversed interval rejected.
- equal interval rejected.
- missing source rejected.

Workflow boundary 5/5:
- fenced gate precedes any future publisher promotion.
- READY remains required.
- no direct publish/commit exists in workflow.
- job ID + lease generation are mandatory in gate.
- queue self-test remains independent.

IMPLEMENTATION: .github/workflows/kwai-real-publish.yml now checks out repository and executes kwai_real_publish_promotion_gate.py for the queued-publication contract. Final publication guard remains closed until external kwai-login/session READY.
NO_REAL_PUBLICATION: true.
