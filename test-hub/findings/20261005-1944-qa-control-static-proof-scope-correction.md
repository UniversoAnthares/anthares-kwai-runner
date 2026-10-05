# QA correction: no-PC static proof does not prove queue transition safety
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388406583
JOB: 112027374829
COMMIT: 96fcee7267c1086ecf647fa74ec316376d62339b
SUPERSEDES: none

## Objetivo
Auditar o alcance exato do finding 20261005-1942-control-plane-no-pc-static-proven.md.

## Resultado
O run prova estaticamente a remoção de local/PC/Google das prioridades e a presença das funções de lifecycle/dedupe. Ele NÃO prova a segurança semântica de complete()/reconcile(): o teste usa grep para presença de async complete/reconcile e não executa casos de confirmação prematura. O código atual ainda aceita confirmed=true sem exigir publication_started=1/status adequado/evidência forte.

## Evidência decisiva
Job 112027374829 verifica `grep -q 'async complete('` e `grep -q 'async reconcile('`, mas não chama essas funções nem testa rejeição. Leitura do snapshot após o run confirma que complete() só exige owner antes de aceitar b.confirmed e reconcile() não restringe confirmação ao estado uncertain.

## Consequência
Preservar como PROVEN somente o escopo no-PC/failover estático do finding 1942. A expressão "invariantes centrais validadas" é ampla demais; queue transition safety permanece PARTIAL conforme 20261005-1935-qa-central-confirmation-invariant-gap.md. CHAT 4 deve adicionar testes comportamentais negativos antes de fechar esse subitem.