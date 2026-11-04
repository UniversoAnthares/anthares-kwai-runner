# Reparo Telegram do WordPress — staged
STATUS: PARTIAL
AREA: wordpress-telegram
DATE: 2026-11-03
RUN: none
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/220
COMMIT: ef5f3a081ceac1b01069a7e552af5c8e9c7556fc
SUPERSEDES: test-hub/findings/20261103-telegram-site-share-relay-lease.md

## Resultado
Branch de correção isolada com 3 arquivos PHP/JS/CSS. Endereço do tópico do fórum é preservado pelo parâmetro anthares_topico_id. Mensagem genérica removida. Botão manual copia texto+link e abre grupo para confirmação humana. Painel agora é recolhível (61px fechado) e modal é breve. Preflight de saúde do relay protege a vinculação; envio exige ok e revogação local depende de confirmação remota.

## Evidência
PR #220. JavaScript compilado via new Function em ECMAScript. Nenhum teste de produção ou publicação foi realizado. CI Vercel reportou failure sem evidência de causalidade, não classificá-lo como aprovado. Lint PHP e QA funcional permanecem pendentes.

## Consequência
Não implantar até executar php -l, manifest preflight e QA e reconciliar estado do branch/main. Relay da Railway permanece indisponível segundo a captura, sem acesso de administração confirmado. Não confundir alteração do GitHub com produção. Lease encerrado; qualquer alteração subsequente exige novo lease e revisão de HEAD.
