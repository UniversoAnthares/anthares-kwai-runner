# Lease: implantação de código health apenas na função Neon de QA
STATUS: RUNNING
AREA: queue
DATE: 2026-10-24
RUN: none
JOB: Neon QA function build/runtime verification
COMMIT: c526165b0aa20eebc62354782dd97799725bd00b
SUPERSEDES: none
LEASE_AREA: qa-cortes-neon-health-runtime
LEASE_OWNER: ChatGPT current conversation
LEASE_START_UTC: 2026-10-24T17:04:00Z
LEASE_MAX_EXPIRY_UTC: 2026-10-24T17:29:00Z

## Objetivo
Comprovar empacotamento e deploy do código infra/neon-cortes-queue/index.mjs da main na função cortesqueue da branch Neon QA br-quiet-unit-b8w1tqmf. Não invocar métodos com mutação, não usar funções produtivas e não promover nenhum código ao banco principal.

## BASELINE_PROVEN
GitHub main c526165b0aa20eebc62354782dd97799725bd00b; PR #1303 já merged c2b19da44ea27297a7cd6c1924e27d41056a3b60. Neon QA função cortesqueue active_deployment.id=39/completed, branch br-quiet-unit-b8w1tqmf separada de br-crimson-unit-b89nau08. Teste SQL QA das roles Threads/Instagram concluído e finding fechado PR #1306.

## FAILED_AVOIDED
Não acionar funções/canais produtivos ou escrever filas. Não acessar credenciais de produção, não transpor bloqueio prévio de administração Windows/SQL. Não reutilizar zip antigo desconhecido para prod. Nenhum deploy do Worker Cloudflare HA. Respeitar quota de branch QA e preservar jobs externos.

## SUCCESS_SIGNAL
ZIP de apenas index.mjs criado a partir do blob GitHub da main; API Neon confirma deployment novo completed somente na branch QA; função produtiva segue no deployment 39. Registro de package SHA/CRC e resposta de implantação. Invocation GET apenas de rota inexistente, se possível e se não consultar banco.

## FAILURE_SIGNAL
Build failure ou erro de empacotamento; estado anterior de função QA diverge, branch ID errado, URL apontando para branch produtiva ou risco de segredo/DB principal.

## TEST_VALIDITY
Deployment completed comprova build/bundle/entrada aceitos na branch QA, não prova execução health, SQL produtivo, migração de roles, URL externa, publicação nem permissões Windows. O runtime herdado pode guardar variáveis que devem ser verificadas antes de qualquer GET com consulta DB.

## Consequência
Lease de homologação com expiração e fechamento append-only obrigatórios. Não usar esta operação para declarar item 6 concluído ou promover production/cutover.
