# Git provider automatic sync enabled
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-07
RUN: scheduled task Anthares Git Mirror
JOB: hourly
COMMIT: pending
SUPERSEDES: none

## Objetivo
Fornecer sincronizacao automatica GitHub<->GitLab sem depender de minutos privados do GitHub Actions nem de pull mirroring Premium do GitLab.

## Resultado
Foi habilitada uma tarefa horaria que usa diretamente os conectores autenticados GitHub e GitLab para os oito repositorios UniversoAnthares. A politica e fail-closed: propaga somente quando um unico lado mudou desde o ultimo estado comum comprovado; divergencia bilateral ou ancestralidade incerta bloqueia sobrescrita, registra finding e notifica. Nao usa PC, force-push ou secrets expostos.

## Evidencia decisiva
Tarefa Anthares Git Mirror criada e habilitada com frequencia horaria. Antes da ativacao, os oito repositorios foram confirmados no GitLab e o conteudo de main de anthares-kwai-runner foi verificado byte-a-byte com DIFF_COUNT=0 apos sincronizacao.

## Consequencia
A redundancia automatica passa a ter transporte independente de GitHub Actions/GitLab Premium. GitLab pull mirror nativo permanece fora da arquitetura Free; push mirror nativo pode ser adotado futuramente se houver credencial GitHub dedicada, sem substituir a protecao contra divergencia.
