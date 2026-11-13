# Kwai: Neon production 77 — endpoint terminal de leitura implantado
STATUS: PROVEN
AREA: kwai
DATE: 2026-11-13
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43522789422
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43522789422/job/132220965782
COMMIT: c9d5d9fb1cdb408e8aa23c081938124b8f0851c7
SUPERSEDES: 20261113-kwai-terminal-local-ack-readonly-ci-proven.md

## Implantação real
- PR #2593 merged, SHA c9d5d9fb1cdb408e8aa23c081938124b8f0851c7.
- Empacotados no Neon os 4 módulos do import graph da main: index.mjs, kwai-pacing-policy.mjs, kwai-persistent-cloud-identity.mjs, kwai-oneoff-public-reconcile.mjs. ZIP em memória, método STORE, sem staging no PC e sem credenciais.
- QA Neon project anthares-ara-ha branch br-silent-mud-b8fzvqta: deployment 11 completed/active, GET ?action=health com ok=true/database_ok=true.
- QA POST sem assinatura em kwai-job-terminal-read: HTTP 401 (acesso negado).
- Produção Neon branch br-crimson-unit-b89nau08: deployment 77 completed/active, GET ?action=health ok=true/database_ok=true.
- Produção POST sem assinatura: HTTP 401.
- Environment preservado pelo deploy_function sem parâmetro environment; acesso admin e RLS permanecem inalterados.

## Integridade e fila
SQL read-only imediatamente antes e depois do deployment 77:
principal 608 confirmed, 16 queued, 14 failed, 2 cancelled;
secundária 48 confirmed, 52 queued, 1 failed, 5 cancelled.
Nenhuma nova publicação, lease ou mutação da fila foi executada nesta operação; nenhuma assinatura física foi enviada.

## Restrições / pendências
A verificação com a assinatura RSA real do executor foi impedida pelos controles de segurança da ferramenta remota. Essa recusa foi respeitada sem tentativas alternativas. Ainda não existe prova real de retorno terminal autorizado em QA/produção. O daemon Windows que atende as duas contas ainda executa código antigo e contém quatro ACKs locais obsoletos (3 confirmed, 1 cancelled no Neon); nenhuma troca de processo foi feita. Não declarar operação retomada nem atualização local concluída. Revisar autorização e homologação antes da atualização do daemon. Zero custo novo; Oracle, CutMotions, cloud Android e executor Android GitHub continuam excluídos.

SQL/RLS production permanece relrowsecurity=false, pg_policies=[] e health rls_attested=false. Corrigir em trabalho isolado de identidade e política com QA, preservando as demais redes.

SUCCESS_SIGNAL: deployment 77 active, health ok, 401 anônimo, counts intactos.
FAILURE_SIGNAL: alteração inesperada de fila, publicação não autorizada, RLS alegado comprovado sem prova.
TEST_VALIDITY: CI 37 Node PASS + regressão AST Python, saúde read-only e SELECT produção.
