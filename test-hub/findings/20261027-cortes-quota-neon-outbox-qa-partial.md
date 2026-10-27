# CORTES-QUOTA-01 — cancellation-first and fenced Neon outbox (isolated QA)
STATUS: PARTIAL
AREA: architecture / quota-cancel-failover
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40496796163
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40496796163/job/122164286587
COMMIT: 3bdcb00698356eb0882cf0a42a5592432c3ba59c
SUPERSEDES: none

## Objetivo
Quando o provedor parar uma execução/job por quota comprovadamente esgotada, solicitar o cancelamento do job próprio imediatamente, confirmar o estado terminal, reconciliar quaisquer efeitos externos e então entregar a tarefa à primeira redundância autenticamente independente. A identidade e o controle global de publicação devem permanecer estáveis.

BASELINE_PROVEN: CORTES usa Neon como autoridade de fila, dedupe por plataforma/conta, limites próprios de cada rede e controles de idempotência. 
FAILED_AVOIDED: novo envio antes de confirmar stop/recibo; cópia de mídia; mudança de conta; fallback reutilizando quota compartilhada; interrupção de workflow compartilhado.
SUCCESS_SIGNAL: CI sem falhas; DDL aditivo em Neon QA; transferência em outbox única; teste sem registros residuais.
FAILURE_SIGNAL: publicação repetida, status de confirmação sem recibo, transição sem fencing, alteração de quotas de plataforma ou DDL em produção durante auditoria.
TEST_VALIDITY: testes unitários CI + teste SQL transacional em QA; não são teste de cancelamento remoto real nem de implantação produtiva.

## Resultado comprovado
- PR #211 e #212 do Anthares Clipper integradas ao branch main. Commits 2c729cf59ef0bc3786076f60564c8bd3c95863ca e 3bdcb00698356eb0882cf0a42a5592432c3ba59c.
- CI run 40496796163: 18 testes do cancelamento + 8 testes do Store PostgreSQL + 9 testes da outbox; 35 testes PASS, nenhuma falha.
- Neon QA branch br-quiet-unit-b8w1tqmf: migração aditiva concluída em QA. Teste de evento+outbox dentro de subtransação reversível passou; SELECT após rollback confirmou 0 linhas para ambos os identificadores do teste.
- Branch QA br-rapid-butterfly-b8okdd6e já possuía tabela cortes_quota_handoff_outbox em layout incompatível. A tentativa da migração foi rejeitada pela coluna ausente outbox_id e a transação foi revertida. Essa tabela foi preservada.
- PR de governança universal #44: https://github.com/UniversoAnthares/anthares-governance/pull/44. Manifesto SHA-256 recalculado, versão proposta 7be5d82f51319a8b. Workflow de governança 40497559248 falhou pré-runner (runner_id=0, sem etapas). Revisão humana requerida.

## Pendências
1. Homologar a migração na base Neon produtiva pelo procedimento de migração autorizado, verificando o esquema atual, permissões mínimas e a ausência de conflitos.
2. Instalar o controlador em processo cloud independente, com credenciais e auditoria de cancelamento efetivo por provedor; não habilitar publicações de teste.
3. Conectar as entregas da outbox ao transporte real com recibos por conta, master, ID externo e reconciliação antes de cada tentativa.
4. Corrigir a divergência do esquema QA antigo por migração explícita ou isolamento definitivo; jamais sobrescrevê-lo às cegas.
5. Aprovar e sincronizar a governança central via policy.py sync/audit; nenhuma aprovação/deploy foi presumida.

## Consequência
STATUS permanece PARTIAL até haver prova de cancelamento e handoff real sem duplicação e sem intervenção no computador pessoal. Não declarar 35 testes unitários como publicação ou implantação produtiva.
