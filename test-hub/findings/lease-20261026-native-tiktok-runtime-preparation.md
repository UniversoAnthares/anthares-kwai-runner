# Lease — native runtime credential preparation
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-26
RUN: none
JOB: iso06-native-runtime-pilot-20261026
COMMIT: 513c8f4015a1c40c7a070f1648b1bb136e163e58
SUPERSEDES: none
EXPIRES_UTC: 2026-10-26T19:55:00Z
OWNER: codex
BRANCH: codex/iso06-native-tiktok-runtime-20261026

## Scope
Only draft source changes in the two lucasrosalem4 workflows, a migration runbook and native credential manifest on this branch. No main changes, workflow dispatch, environment/secret provisioning, credential read, publication, queue, RLS, profile or deployment mutation.
User explicitly adopted BWS administrative custody plus provider-native isolated runtime credentials with zero cost. Existing production runs are preserved.

## Baseline
Main source SHA above; cloud workflow blob19d6cb6c2172025be30b502184b02670a34510a6, fallback blob9ba07142ef7676dfcdff027e600e074482a0d896. Native account Environment not proven provisioned. Previous administrative GitHub/credential operations have specific refusals: do not reproduce through another channel. Existing diagnostic Environment is not release IAM proof.

## Avoided failures and validity
Do not reuse repository-wide secret names under a new Environment: GitHub secret fallback would defeat missing-secret detection. Use a distinct native secret reference while retaining the existing process variable. No BWS token enters either workflow. Preserve triggers, concurrency, existing main guards and OIDC permissions.
No code from this branch may run a publisher as verification. Static YAML and established offline contract only. Neither result authorizes cutover.

## Signals
Success: two YAML patches contain exact native Environment/name, fail closed when native input missing, and retain event/concurrency contracts; negative source checks reject BWS/foreign credentials.
Failure: stale base, unsafe diff or tests fail; no production integration.
Rollback: discard draft branch, no runtime rollback needed. Later production rollback requires governance review and restored previous reference; never auto-fallback to a shared credential.
