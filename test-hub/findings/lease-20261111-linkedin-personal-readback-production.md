# Lease operacional — LinkedIn pessoal, reconciliação sem novo upload
STATUS: RUNNING
AREA: linkedin-personal-production-readback
DATE_UTC: 2026-11-11
OWNER: chatgpt-cortes-20261111-readback
BASE_HEAD: eb4ff6f3d3b1c87ca8109de9e2ea710643514ad9
BASELINE_PROVEN: LinkedIn personal confirmed 139, uncertain 1, latest remote urn:li:ugcPost:7526240278874095616; existing workflow primary does public readback + new publication in same run. GitLab peer content matches GitHub primary workflow.
FAILED_AVOIDED: no readback through disabled standby; no direct UPDATE Neon; no duplicate upload; no test suites, no new secrets, no Android or PC execution.
SUCCESS_SIGNAL: explicit main workflow_dispatch reconcile_only confirms remote public embed through existing reconcile_personal(), preserves existing scheduler, and verifies no media upload in that mode.
FAILURE_SIGNAL: extra upload from readback-only invocation, untrusted remote URL, authentication failure, pending account paused, conflicting work.
TEST_VALIDITY: live operational readback only; no synthetic tests or test infrastructure.
CLOSED_LEASE: false
