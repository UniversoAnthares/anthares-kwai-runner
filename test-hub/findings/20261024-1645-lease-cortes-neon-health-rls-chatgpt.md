# Lease: CORTES — correção health SQL e QA de RLS por rede
STATUS: RUNNING
AREA: queue
DATE: 2026-10-24
RUN: none
JOB: ChatGPT — continuidade do item 6
COMMIT: fb93e2d21180aaa31b314fc6963e8641eadcc377
SUPERSEDES: none
LEASE_AREA: queue-health-rls-readiness
LEASE_OWNER: ChatGPT current conversation
LEASE_START_UTC: 2026-10-24T16:45:00Z
LEASE_MAX_EXPIRY_UTC: 2026-10-24T17:10:00Z

## Objetivo
Concluir os testes SQL de segregação em Neon QA e corrigir a afirmação de isolamento SQL não comprovado na resposta health de cortesqueue. Não realizar migração, deploy, publicação ou cutover produtivo.

## BASELINE_PROVEN
Neon main purple-flower-35918989 / br-crimson-unit-b89nau08: 14 tabelas cortes_* sem RLS/policies, runtime com papéis BYPASSRLS, inspeção no Plano Mestre Anexo V. Branch QA br-quiet-unit-b8w1tqmf: RLS de tabela sintética e testes reais bidirecionais SELECT, INSERT, UPDATE (permitidos no mesmo destino e negados no cruzado). GitHub main fb93e2d21180aaa31b314fc6963e8641eadcc377, PR draft #1303 head 88ba34b133ba1c671319d048045f9a9a568fbec1. O projeto tem CI GitHub concorrente X Cloud Full Flow na main, área independente; espelho GitLab divergente duo-main sem os arquivos alvo.

## FAILED_AVOIDED
Não contornar recusa do Anthares Remote/ARA para preflight/ACL Windows. Não consultar handoff Threads negado nem dados de fila protegidos por outro caminho. Não alterar RLS/grants em produção, DATABASE_URL, escritores, credenciais ou publicações; não disparar o workflow de deploy Cloudflare HA acidentalmente. Não supor que network_isolation:true prova RLS.

## SUCCESS_SIGNAL
Contratos da PR comprovam alteração somente health/testes/atestado de HA; nenhum deploy automático na merge. Evidências SQL QA bidirecionais, códigos de revisão GitHub, checksum de blobs e documentação atualizada. CI de código somente quando for executável dentro das permissões.

## FAILURE_SIGNAL
Workflow altera publicador/lease, HEAD ou blob concorrente, deploy Cloudflare disparado pelo merge, política SQL falha em negação cruzada, ausência de lease exclusivo ou autenticação negada.

## TEST_VALIDITY
Leitura do código/asserções estáticas não comprova deploy. O health novo só valerá em produção após deployment Neon separado. QA sintética não comprova isolamento SQL produtivo nem publicação real. Não classificar CI não executado como PASS.

## Consequência
Esta é apenas reserva temporária de área de alteração, máximo de 25 minutos. Revalidar HEAD e outros leases antes de escrever. Fechar com finding append-only PROVEN/PARTIAL e SUPERSEDES deste arquivo; não manter lease RUNNING eterno.
