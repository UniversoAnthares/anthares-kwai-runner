# Política obrigatória: read-before-write
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

Para qualquer alteração GitHub/GitLab, o agente deve:
1. Ler arquivo integral no provedor de destino e registrar SHA de blob, SHA do HEAD, projeto, branch e instante da leitura.
2. Comparar conteúdo e histórico do arquivo nos dois provedores antes de reconciliar; jamais assumir equivalência por nome.
3. Preparar patch mínimo, conferir lease e reler HEAD imediatamente antes do commit.
4. Usar escrita condicional por SHA/commit-base; se o SHA mudou, ABORTAR e reler/recalcular patch. Nunca force push nem reset de branch compartilhada.
5. Abrir MR/PR com revisão e testes; proteger main e exigir pipelines/status checks, bloquear pushes diretos por agentes.
6. Somente após merge verificado replicar commit para outro provedor, com fast-forward ou integração revisada.
7. Publicações reais exigem ledger/idempotência e confirmação remota; jamais reexecutar após falha incerta.
8. Registrar findings append-only sem secrets.

ATENÇÃO: política documental não substitui branch protection/rulesets configurados nos dois provedores. Até prova desses controles, STATUS=PARTIAL.
