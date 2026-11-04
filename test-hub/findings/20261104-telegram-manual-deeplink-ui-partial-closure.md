# Telegram WordPress — fluxo manual com rascunho em grupo
STATUS: PARTIAL
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: isolated JS/PHP smoke (model container); no live app test
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/221
COMMIT: e643e7a74a88f3ba7d8ba759fde4361b399ae56b
SUPERSEDES: test-hub/findings/20261104-telegram-manual-deeplink-ui-lease.md

## Baseline
O site abre https://t.me/universoanthares00 como preview, sem entrar no chat. O formulário WordPress já exige mensagem, mas o fallback abre o preview. O relay Railway permanece FAILED na diretiva Docker VOLUME, bloqueando vinculação e envio autenticado.

## Mudança proposta
PR #221 draft em branch isolada modifica somente o PHP e JS do formulário Telegram para construir o deep link oficial tg://resolve?domain=universoanthares00&text=... com mensagem e link do tópico; fallback manual Web copia mensagem e abre web.telegram.org/k/#@universoanthares00. Retém input obrigatório, limite 2.000 caracteres, fluxo AJAX vinculado, toggle e parâmetros do tópico. Bump de cache -tg-20261104d.

## Evidência
GitHub PR #221 tem 2 arquivos alterados (PHP/JS), base main 6a76d0f62d9dcb5544609906a3e222ea20929690, HEAD e643e7a74a88f3ba7d8ba759fde4361b399ae56b.
Contrato oficial: https://core.telegram.org/api/links documenta tg://resolve?domain=<username>&text=<draft_text>.
Smoke isolado node --check e execução URLSearchParams PASS para username, conteúdo do tópico e URL codificada; PHP lint e execução isolada de regex/URL PASS. Esses smokes validam snippets, não os arquivos completos. Vercel status da PR= failure por deploy account blocked; sem GitHub Actions QA adicional nesta PR.
Relay PR #5 anterior possui remoção VOLUME e idempotência pending/confirmed/uncertain; PR #6 draft acrescenta chown+gosu no volume. Coordenação de conflito relatada em comentários de #5/#6. Custo Railway R$0 sem prova e dois projetos fonte main, portanto nenhuma implantação ou novo serviço.

## Resultado e pendências
Nenhuma publicação Telegram real foi gerada. PR #221 segue draft, sem merge e sem deploy; site ainda usa código anterior. Validar lint PHP integral, parser JS integral, QA de manifesto, deploy WordPress com backup e teste controlado de rascunho no Telegram real. Para envio em um clique: reconciliar relay PR #5/#6, comprovar custo zero e volume/segredos, implantar apenas um serviço e testar MTProto com conta controlada. Só então confirmar vinculação e envio.
Lease encerrado em estado PARTIAL.
