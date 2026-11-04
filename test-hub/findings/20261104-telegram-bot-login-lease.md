# WordPress Telegram — login verificado e compartilhamento HTTPS
STATUS: RUNNING
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: no live send
JOB: User-requested repair, 2026-11-04
COMMIT: WP main aff7ab91cf2c12c7e26af370e38f97e8cde72473
SUPERSEDES: test-hub/findings/20261104-telegram-wordpress-manual-live-proven-relay-blocked.md

## Objetivo e baseline
Corrigir botao tg:// que depende do handler Telegram Desktop nao presente e vinculo MTProto cujo relay Railway estah offline. Site Hostinger tem bot @anthares2_bot existente, com credencial privada no option wptelegram, Bot API getMe comprovou autenticacao valida e getWebhookInfo sem webhook, nenhum segredo sera exposto. Usar Telegram Login Widget oficial e HMAC server-side sem servico novo; HTTPS share/url com escolha do grupo. Preservar fallback MTProto, grupos, texto obrigatorio, topicos e CSS.

## FAILED_AVOIDED / SUCCESS_SIGNAL / VALIDITY
Evitar outra tentativa do mesmo deep link tg:// e ativacao Railway sem custo zero comprovado. Realizar QA PHP lint JS syntax, manifest 605/605 e deploy com backup, WPCLI render e hash HTTP. Exito do login real depende da configuracao @BotFather do dominio; sem autenticacao real nao afirmar vinculo completo. Nao publicar mensagens automaticamente nem gerar cobranca.

## Lease
Exclusividade wordpress-telegram por 25min desde 2026-11-04T12:59:45.690Z.