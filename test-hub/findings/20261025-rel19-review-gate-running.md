# REL-19 — controlador independente de revisão de pacote ZIP (preflight)
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-25
RUN: none
JOB: REL19-20261025
COMMIT: db6c12fdaa0af01e3b68b8a527b2e02c12c21837
SUPERSEDES: none
LEASE_AREA: cortes-release-review-readonly
LEASE_OWNER: ChatGPT-REL19
LEASE_BASE: anthares-clipper/main@db6c12fdaa0af01e3b68b8a527b2e02c12c21837
LEASE_SCOPE: adicionar modulo independente de atestacao read-only, seus testes exclusivos e documentacao em branch platform/rel19-review-gate-20261025. Nenhuma alteracao de publicador/CI/filas.

## BASELINE_PROVEN
Gerador e verificador existentes na main. Historico REL-02: 28 testes integrados PASS (registro 25/10/2026), com ressalvas operacionais; release_verifier possui 17 testes adversariais.

## FAILED_AVOIDED
Nao executar as suites restritas release_candidate, workspace_export, workspace_factory ou instagram_uncertain_triage; nao alterar CI existente, workers, runner, seguranca do provedor, credenciais, deploy, banco ou publicar. Nao reutilizar a recusa de teste por outro canal. Divergencia documental local INDICE.md (f6fc9ca59a96e451) versus GitHub main (2e28d54043d6bad1) preservada.

## SUCCESS_SIGNAL
Modulo isolado adicionado em branch, testes proprios PASS sem executar codigo de pacote, recibo sempre review_only e deploy_authorized=false, com caminho confiavel fora da raiz do agente e hash SHA256 externo.

## FAILURE_SIGNAL
Erro de permissao, referencia instavel, validação negativa ausente, conflitos de arquivos ou teste falho: manter DRAFT/partial, sem deploy.

## TEST_VALIDITY
Contrato e QA local do controlador read-only; nao prova IAM/ACL/RLS, controle de promocao obrigatorio, protecao de main, rollback, rede social real ou ativacao de publicador.
