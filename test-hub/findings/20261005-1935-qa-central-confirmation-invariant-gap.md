# Central queue complete/reconcile still trusts caller confirmation too broadly
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: static-readonly-audit
COMMIT: 7dd99a42ab0ae955f996c0c540a72567a301d5ea
SUPERSEDES: none

## Objetivo
Auditar invariantes de confirmação durante o lease cloudflare-control ativo, sem mutar a área.

## Resultado
No snapshot auditado, complete() aceita confirmed=true para qualquer job cujo owner coincida, sem exigir status='leased', publication_started=1, remote_id não vazio ou evidence token. reconcile() também aceita confirmed=true quando owner está vazio ou coincide, sem exigir que o job esteja uncertain. A proteção do workflow Kwai reduz risco no chamador, mas o controlador ainda não impõe sozinho a invariável de confirmação positiva.

## Evidência decisiva
cloudflare-worker/src/index.js: complete() testa not_found e owner, depois grava status='published', confirmed=1 quando b.confirmed; não testa j.status/publication_started/evidência. reconcile() grava published quando b.confirmed e não restringe o estado anterior a uncertain.

## Consequência
CHAT 4, dentro do lease atual, deve fechar no controlador as transições permitidas. Sugestão de invariantes: complete confirmado somente de leased + publication_started=1 + evidência/remote_id conforme contrato; reconcile confirmado somente de uncertain (ou estado explicitamente reconciliável). Self-test deve provar rejeição de confirmação prematura. Até isso ocorrer, queue safety é PARTIAL mesmo com o hardening do chamador.