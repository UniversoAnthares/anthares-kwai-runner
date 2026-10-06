# 30-way final expansion after failed canaries
STATUS: RUNNING
DATE: 2026-10-06
AREA: tiktok-publish, kwai-login

## TikTok
The prior v14 chain failed before irreversible publication. The latest restore/preflight path showed the common protected-boundary failure before the canary. The workflow is now expanded to 30 independent read-only OIDC/control/Render boundary replicas. The preflight no longer depends on the single restore job, so all 30 emit their own HTTP boundary evidence even when restoration fails. The irreversible lean-v14 job remains serialized behind the matrix and safety gates.

SUCCESS_SIGNAL: at least one causal class is isolated across 30 independent boundary observations, followed only by the existing single fenced canary.
FAILURE_SIGNAL: all 30 share the same protected-boundary failure, proving the executor is not the cause and forcing replacement of that authorization/session transport.

## Kwai
The previous real autologin acceptance failed inside disposable Android acceptance after vault/credential/KVM setup. The same real acceptance is now expanded to 30 isolated Android replicas. Each has its own emulator and uses the validated vault and existing secret-backed credential flow. No publication is performed by this matrix.

SUCCESS_SIGNAL: any replica reaches authenticated READY evidence.
FAILURE_SIGNAL: all 30 converge on the same login/challenge boundary, which promotes persistent cloud session/bootstrap as the replacement mechanism.

## Safety
Parallelism is diagnostic/authentication only. Real publication remains single, fenced, READY-gated and independently reconciled.
