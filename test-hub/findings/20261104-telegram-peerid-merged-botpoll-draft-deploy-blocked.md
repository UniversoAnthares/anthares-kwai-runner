# Telegram — link do grupo corrigido no GitHub; confirmação via bot preparada
STATUS: PARTIAL
AREA: wordpress-telegram
DATE: 2026-11-04
RUN: GitHub PR 225 merged; PR 226 draft; live deployment not attempted after explicit tool denial
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/225
COMMIT: 31ac0ef0ad827be346760e5f57625d3bb2d218bb
SUPERSEDES: test-hub/findings/20261104-telegram-web-peerid-on-demand-poll-lease.md

## PROVEN
Bot API getChat @universoanthares00 confirmed -1001152484758 on both existing bots. Web A expects peer -1152484758; old #@username opened blank chat. PR #225 merged to WordPress main: PHP data-group-web-id and JS webGroupUrl using verified numeric peer; JS parser PASS and click simulation opened https://web.telegram.org/a/#-1152484758 and copied message plus topic 10898 link. **Não foi homologado no browser autenticado**.

## PARTIAL
Existing @anthares2_bot via getUpdates without webhook returned API_OK yes and 0 pending. PR #226 DRAFT prepares on-demand Bot API polling and /start signed challenge mapping, no webhook registration. Needs security/QA PHP, concurrent bot polling and real user auth test. Flag anthares_telegram_bot_polling_ready remains disabled; user sees old linkage error in production.

## Blocker
A tentativa de executar QA pelo SSH da Hostinger foi expressamente bloqueada pelas configurações de segurança da ferramenta; a execução foi interrompida, sem utilizar outro canal para contornar. Nenhum deploy Hostinger ocorreu nesta tentativa. Palavra 'implantado' NÃO se aplica à PR 225 em produção: é apenas merge no GitHub. Sem custo novo e sem mensagens enviadas.

## Próximo
Executar QA e implantação autorizados quando os controles permitirem, com backup, comparação de SHA e WPCLI, ativar o modo polling sem modificar webhook anterior; confirmar link do grupo no navegador autenticado e vinculação real; depois tratar separadamente o envio como conta pessoal MTProto.
Lease concluído PARTIAL.