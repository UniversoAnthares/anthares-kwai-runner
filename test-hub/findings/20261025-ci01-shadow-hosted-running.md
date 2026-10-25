# CI-01 SHADOW-01 — validação GitHub hosted sem credenciais
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-25
RUN: none
JOB: ci01-shadow-readonly-20261025
COMMIT: 4e413afd669de8f5ca437926887dc1f0562f65cf
SUPERSEDES: none
LEASE_AREA: cortes-shadow01-hosted-ci
LEASE_OWNER: ChatGPT-Universo-Anthares
LEASE_BASE: anthares-clipper/main@d87118e2cb844369bcf7a9341624b7ef83454d29
LEASE_SCOPE: adicionar somente workflow isolado de QA com permissões contents:read, runner ubuntu-24.04, 27 testes SHADOW-01 e artefato de log sanitizado.
LEASE_STATUS: RUNNING

## BASELINE_PROVEN
tests/test_network_shadow_cutover.py já versionado na main do Clipper, 27 casos PASS no Windows. CI geral network-offline-regressions.yml permanece exclusivamente manual, com 15 suítes de escopo distinto e runner Windows.

## FAILED_AVOIDED
Não executar quatro suítes explicitamente restritas (instagram_uncertain_triage, release_candidate, workspace_export, workspace_factory), não invocar publicação, secrets, SQL, APIs de mídia, deploy, workflows de outros sistemas, nem alterar CI existente/runner Windows.

## SUCCESS_SIGNAL
PR com somente um workflow de QA para shadow; GitHub-hosted Ubuntu realmente inicia, executa 27 testes PASS, publica log e termina success; merge no main somente após checagem.

## FAILURE_SIGNAL
Job sem runner -> PARTIAL/NOT_TESTED; 27 falhando -> FAILED e manter sem merge; falha de API/race -> reconciliar, sem repetição cega.

## TEST_VALIDITY
Somente auditor offline, snapshots sintéticos; mesmo CI verde continua sem autorizar cutover ou certificar IAM, RLS, ACL, writer único e post externo.
