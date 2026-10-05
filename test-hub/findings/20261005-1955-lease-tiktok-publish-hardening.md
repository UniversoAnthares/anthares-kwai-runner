# Lease TikTok publish hardening
STATUS: RUNNING
AREA: tiktok
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

LEASE_AREA: tiktok-publish
OWNER: CHAT-3
EXPIRES_AT: 2026-10-06T00:25:00Z
BASELINE_PROVEN: publisher exige STATE+VERIFIED; local publisher espera confirmação UI e grava evidence confirmed; sessão atual está bloqueada fail-closed.
FAILED_AVOIDED: não disparar canário sem sessão; corrigir endpoint público antigo; não usar fallback cego após resultado ambíguo.
SUCCESS_SIGNAL: contrato de publicação aponta somente ao Render canônico rootless, faz preflight ready_for_tiktok e mantém publish restrito a workflow_dispatch.
FAILURE_SIGNAL: qualquer rota pode publicar por push, endpoint antigo permanece, ou publicação pode iniciar sem readiness.
TEST_VALIDITY: apenas auditoria/patch estático; nenhuma publicação real nesta lease enquanto sessão não estiver PROVEN.

## Objetivo
Endurecer o caminho de publicação enquanto a sessão aguarda dependência do CHAT 4.
