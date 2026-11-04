# Telegram — grupo Web por ID e vinculação via leitura sob demanda
STATUS: RUNNING
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: user screenshot opens blank Web A on #@username
JOB: ChatGPT request 10:12 AM
COMMIT: wordpress main a6a10f4788da05e3558be374d8b7def4fea92ce5
SUPERSEDES: test-hub/findings/20261104-telegram-group-web-proven-bot-webhook-security-blocked.md

## Escopo / evidências
Bot API read-only getChat @universoanthares00 confirmou supergroup ID -1001152484758 (ambos bots). Web A usa hash de peer MTProto para supergroup: -1152484758. Atual link #@universoanthares00 abre tela sem chat (print do usuário). Bot @anthares2_bot via getUpdates read-only apresentou zero pendências e nenhum webhook. WordPress has /start challenge code, mas BOT_READY=no devido ao webhook que não pôde ser registrado. Adotar confirmação mediante getUpdates sob demanda no AJAX, sem registrar webhook e sem custos; não interferir no bot de discussões (token distinto).

## Regras
Só arquivos do plugin Telegram; lock SHA; PHP lint, JS parser, QA 605/605; backup e rollback; teste de clique + REST; não enviar mensagens ao grupo; não acionar serviço pago. Não registrar setWebhook nem tentar contornar recusa de segurança anterior. Não inferir prova de envio da autenticação.

## Sucesso
link web.telegram.org/a/#-1152484758 testado por clique simulado; bot /start via getUpdates sem webhook, verificação com ID assinado pelo Telegram, sem consumir mensagens alheias (ler sem offset); WP authed nonce + desafio. Homologação real com login e mensagem requer confirmação do usuário.

## Lease
Owner ChatGPT, de 2026-11-04T14:16:44.268Z, até 2026-11-04T14:41:44.272Z; encerrar append-only.