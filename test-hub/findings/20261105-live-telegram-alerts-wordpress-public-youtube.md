# Avisos de lives Universo Anthares — execução e testes
STATUS: PARTIAL
AREA: live
DATE: 2026-11-05
RUN: WP-CLI Hostinger PHP 8.2 — anthares_live_tg_tick
JOB: none
COMMIT: UniversoAnthares/anthares-wordpress@fd3bc2477e4de5f957d504ca48119d948b403977
SUPERSEDES: none

## Resultado
- PROVEN: arquivo `anthares-pix-sales/includes/88-telegram-usuario.php` implantado na Hostinger; blob Git `8d60d7386ce9da9fad67068d84931ad96ee5022e`; `php -l` limpo.
- PROVEN: `wp cron event run anthares_live_tg_tick` executado, estado `ok`, `upcoming_count=1`, live `ODj-n2dB6_Q` às 18h (America/Campo_Grande; timestamp 1793916000); HTML público YouTube 200 com timezone verificado.
- PROVEN: quatro envios interceptados por mock de `pre_http_request`; `texts_exact=true`, `chats_ok=true`, `ledger_errors=[]`, quatro chamadas após duas tentativas por antecedência; zero publicações no Telegram durante o teste.
- PROVEN: WP-Cron agendado a cada minuto e estado atualizado espontaneamente após execução inicial.
- PARTIAL: primeiro envio real pendente das 12h (horário local). WP-Cron depende de tráfego; cron independente do hPanel não foi configurado.
- API YouTube estava pausada por quota e sem chaves acessíveis; fallback público usa o fuso confirmado e não tenta enviar quando há erro/429. Código idempotente preserva reservas de envio incerto.
- Nenhum novo serviço pago, runner Windows, depósito de mídia no PC ou mensagem de teste ao grupo.
