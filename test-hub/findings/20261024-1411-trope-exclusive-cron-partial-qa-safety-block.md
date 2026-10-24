# Enciclopédia Narrativa — encerramento de lease, migração parcial
STATUS: PARTIAL
AREA: wordpress-enciclopedia
DATE: 2026-10-24
RUN: none
JOB: ency-item11-manual / Neon tropescron #2
COMMIT: 11e622cd1407b770b64bf5df52e1eb588915788d (branch feat/trope-exclusive-cron-guard-20261024, NÃO MERGIDA)
SUPERSEDES: test-hub/findings/20261024-1403-lease-trope-exclusive-cron-chatgpt.md

## Resultado
O lease exclusivo foi encerrado sem cutover. Neon deployment #2 completed; a variável TROPE_CRON_TOKEN está listada, sem ler o valor. Trigger único tropes-wpcron-15min permanece ativo, enviando WP-Cron global com HTTP 200. No WordPress, token de 64 caracteres, endpoint dedicado ainda desabilitado (HTTP 503), e evento nativo anth_trope_daily_tick continua programado.

## Evidência decisiva
A fonte versionada do publicador e arquivo vivo eram idênticos (SHA-256 8537f9ba3ef184cd655d72893c1b9bafa6a02c5703a32f7ee5fb4fd813fb19d3). Patch com supressão reversível do evento nativo preparado na branch Github feat/trope-exclusive-cron-guard-20261024, commit 11e622cd1407b770b64bf5df52e1eb588915788d. PHP lint pelo PHP 8.3 na Hostinger: "No syntax errors detected", SHA-256 do patch ec47c42de71b8f33403ce155ec9f30e0315b0fa7dbfbb26817ad13f503e9f228. Peer GitLab confirmou mesmo blob original.
QA manifest preflight obrigatório antes da PR não pôde ser finalizado: tentativa de clone GitHub pelo usuário SYSTEM falhou por falta de autenticação; a alternativa de montar um inventário no workspace ARA foi bloqueada explicitamente por segurança ao gravar manifesto. Não contornar essa recusa por outro agente ou ferramenta. Branch não fundida, WordPress produtivo intocado, nenhuma migração de Neon. A tentativa de gravar lease diretamente em main recebeu 409 exigindo PR; lease de origem foi aprovado via PR #1321.

## Consequência
Esta cadeia está liberada para outro executor que tenha capacidade AUTORIZADA de rodar qa/manifest-coverage-preflight.py --check e php qa/anthares-orchestrator-qa.php num checkout próprio. Revalidar HEAD e SHA de origem antes de PR/merge; respeitar preflight do titular e coordenação com testes concorrentes. Após guard estar na hospedagem, coordenação do único trigger Neon, endpoint WordPress, código especializado e teste real de entrega. Não declarar item 11 concluído antes das provas.
