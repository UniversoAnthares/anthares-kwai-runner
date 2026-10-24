# CORTES SQL RLS em QA e health sem atestado falso — fechamento de lease
STATUS: PARTIAL
AREA: queue
DATE: 2026-10-24
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1303
JOB: ChatGPT / Neon QA br-quiet-unit-b8w1tqmf
COMMIT: c2b19da44ea27297a7cd6c1924e27d41056a3b60
SUPERSEDES: test-hub/findings/20261024-1645-lease-cortes-neon-health-rls-chatgpt.md
LEASE_AREA: queue-health-rls-readiness
LEASE_OWNER: ChatGPT current conversation
LEASE_STATUS: CLOSED

## Objetivo
Fechar o lease de queue-health-rls-readiness com evidência de segregação SQL real em QA e impedir que health de produção declare prova de RLS inexistente. Não promover fluxo de publicação, não tocar o banco principal nem reencaminhar states uncertain.

## BASELINE_PROVEN
Neon projeto purple-flower-35918989, branch produtiva br-crimson-unit-b89nau08: 14 tabelas CORTES sem RLS; papéis LOGIN atuais com BYPASSRLS. Neon branch QA br-quiet-unit-b8w1tqmf com papéis NOLOGIN/NOBYPASSRLS separados para Threads e Instagram, policies USING/WITH CHECK por target_key e tabela sintética com FORCE RLS.
GitHub main anterior à correção: a2d34d6684226f1c054632801b1b4aa71983bb7a. Lease registrado na PR #1304; workflow de HA e PR #1303 reavaliados antes do merge.

## FAILED_AVOIDED
Não usar controle remoto alternativo para contornar recusa de segurança inicial; não consultar handoff Threads negado por outro caminho. Sem RLS/roles/policies produtivas, sem novos LOGIN ou credenciais, sem read de jobs reais, sem requeue/lease/publish, sem canário remoto e sem deploy da Neon Function ou do Worker Cloudflare.

## SUCCESS_SIGNAL
Na tabela sintética, cada papel QA leu 1 registro próprio e 0 do outro antes dos inserts positivos. INSERT próprio e UPDATE próprio de Threads e Instagram tiveram RETURNING com chave e status corretos; UPDATE alheio resultou em zero linhas; INSERT alheio e mudança de target_key foram rejeitados por RLS nos dois sentidos. Readback como owner: dois registros de teste por rede, zero estados proibidos. Auditoria pós-merge GitHub: PR #1303 merged em c2b19da44ea27297a7cd6c1924e27d41056a3b60; blobs em main: worker b9aa74bb339d84bf5fdb985171c69b2e0e1d1a66, Neon source 9fbd66fae884b2aea8fde15a0e4652be09df41ce, testes 372ca8dfd5ed397d27b3941ece127a924f0aeb78. O gatilho push do HA depende somente de infra/cloudflare-cortes-queue-ha/**, não do YAML. Workflow manual preservado. Na consulta feita após merge, zero GitHub Actions runs atribuídos ao SHA; Neon cortesqueue permanecia em deployment 39 (2026-10-22).

## FAILURE_SIGNAL
Qualquer publicação disparada ou alteração inesperada de status/fila seria incidente; nenhuma foi acionada por este procedimento. Produtores e consumidores ainda não possuem role SQL exclusiva, e Neon em produção continua sem prova RLS.

## TEST_VALIDITY
A matriz de QA é PROVEN APENAS para a tabela sintética e papéis NOLOGIN assumidos em SET ROLE. Não há teste de autenticação LOGIN própria por rede; não há CI Node efetivo comprovado da PR #1303, apenas inspeção estática de escopo/contratos e validação de readback de GitHub. O merge não equivale à implantação Neon Function nem à prova da URL health ao vivo. Não transformar zero runs em CI verde.

## Consequência
Lease encerrado nesta área. Fonte de código foi corrigida, mas a Neon Function produtiva mantém deployment 39. Faltam: credencial SQL por runtime e RLS real, ACL/identidades Windows autorizadas, único escritor por rede, evidência editorial assinada, reconciliação de uncertain e canário/rollback de publicação. Ativações precisam de novos leases e de provas de segurança independentes.
