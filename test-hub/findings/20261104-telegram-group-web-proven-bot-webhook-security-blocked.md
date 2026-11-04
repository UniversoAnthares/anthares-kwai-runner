# Telegram WordPress — grupo Web em produção; vínculo por bot pendente do webhook HTTPS
STATUS: PARTIAL
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: Hostinger WP-CLI and public HTTP 200 blob QA; Bot API webhook setup diagnosed
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/224
COMMIT: 042277b285a7814d961f68d729a87dd771d3c915
SUPERSEDES: test-hub/findings/20261104-telegram-bot-start-webhook-lease.md

## PROVEN em produção
A PR #224 foi integrada e os três arquivos Telegram WordPress implantados com lock, backup e rollback preparado. SHA exatos da Hostinger e GitHub:
PHP 41e26914f5e3a7d4f3dbd2abe2ab7c8d6d35e690;
JS dbd725029f10c86445570ddbf518498d21c28170;
CSS 35f8919c70add8dda0831b4e57ea385dcbaa3b82.
JS público retorna mesmo blob. PHP lint 8.5 PASS, manifesto QA 605/605 PASS. WP-CLI com WordPress carregado: GROUP_BUTTON, PANEL_HIDDEN, TOPIC_LINK => PASS. Simulação JS click: abre diretamente https://web.telegram.org/a/#@universoanthares00 e copia mensagem + URL do tópico; sem t.me/share/url.

## Vinculação bot
Código de /start com desafio temporário de 40 caracteres, webhook REST com validação da assinatura por secret_token, polling AJAX e associação de ID de usuário está instalado. Bot preexistente @anthares2_bot válido; separado do bot do plugin de discussões. Endpoint HTTPS de webhook sem header retornou HTTP 401 (rejeição correta).
Status BOT_READY=no; autenticação real ainda não funciona.
A tentativa inicial de registrar webhook falhou com erro Bot API 400 "An HTTPS URL must be provided for webhook", pois rest_url em WP-CLI retornou http. Correção operacional identificada: usar set_url_scheme(rest_url(...), 'https'). A ação de registro HTTPS foi **bloqueada pelas configurações de segurança da ferramenta OpenAI**, portanto foi interrompida imediatamente, sem tentar outro canal. Nenhuma mensagem de grupo enviada. Nenhuma despesa nova.
PR anterior #223 do login widget foi encerrada como superseded para evitar merge conflituoso.

## Próximo bloqueio
Registrar webhook HTTPS com o bot em sessão administrativa autorizada, sem contornar a recusa de segurança desta execução; depois testar /start real e confirmação da conta. O envio automático pela conta pessoal continua dependente da sessão MTProto e do relay remoto sem custo. Lease encerrado PARTIAL.