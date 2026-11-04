# Cloudflare Workers/ARA — pacing de chamadas ociosas preparado
STATUS: PARTIAL
AREA: cloudflare-quota / ara-agent-poll
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T13:00:07.988Z
RUN: none
JOB: none
COMMIT: baf154567e61d28358decac3c7631cf4ed3d4485
SUPERSEDES: 20261104-lease-cloudflare-ara-idle-poll-quota.md
LEASE_AREA: ara-agent-cloudflare-idle-poll-pacing
LEASE: CLOSED
GOVERNANCE_MANIFEST: 223433740e807a90

## Fato confirmado
O email oficial da conta anthares1 relata esgotamento do limite de 100000 entradas diárias de Workers/Pages em 2026-11-03. O Go client no main executa um GET ocioso a cada 2 segundos e, com erro, novo GET após 3 segundos. URLs diretas de *.workers.dev aparecem em wrappers legados de ARA. A quota de requisições é compartilhada pela conta e o monitoramento por Worker ainda não está disponível neste conector.

## Implementação isolada
Nova função quota_pacing.go seleciona para HTTPS *.workers.dev 15 segundos entre consultas ociosas e 60 segundos após falha; para outros controladores preserva 2/3 segundos. main.go muda apenas as duas chamadas time.Sleep; nenhuma rota, autenticação, credencial, scheduler, mídia ou processo remoto é alterado. Conflitos potenciais com as PRs antigas #1808 e #1920 devem ser reconciliados, sem sobrescrita.

## Prova
Go standard library em sandbox isolado: oito cenários PASS, executados sem qualquer chamada Cloudflare ou Actions. Readback via GitHub branch confirmou os três arquivos e o blob de main.go `65e59210a2bb42cdd2b24c9ae74d192e69bf3a65`. Um agente: até 44640 chamadas diárias anteriores (43200 polls + 1440 heartbeat); 7200 após (5760 polls + heartbeat), redução potencial 83,87%. Erros reduzidos de 28800 para 1440 tentativas/dia (95%), se a situação persistir por 24h. Uso real e identidade do maior consumidor permanecem UNVERIFIED.

## Portas para DONE
Incorporar após revisão e coordenação com duas PRs de wake, compilar e atualizar o executor autorizado do ARA, depois conferir relatório diário Cloudflare por Worker sem gastos. Até isso, o estado é STAGED/PARTIAL; economia real não foi comprovada. Não executar Windows como runner ou storage de trabalho. Rollback: reverter PR, preservando serviços.
