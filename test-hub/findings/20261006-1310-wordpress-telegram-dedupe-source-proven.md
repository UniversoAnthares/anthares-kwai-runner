# WordPress Telegram dedupe gap closed in source
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: 484dad7d552e596110a55ca41d57813574c9174c
SUPERSEDES: none

## Objetivo
Fechar a lacuna observada no botão "Enviar para o grupo do Telegram": retries/refresh geravam request_id novo em cada chamada.

## Resultado
anthares-pix-sales/includes/88-telegram-usuario.php agora deriva request_id opaco e determinístico de usuário + connection_id + chat + texto + janela de 10 minutos, assinado com wp_salt. O texto não é exposto na chave. Mensagens diferentes continuam com chaves diferentes; retry idêntico dentro da janela reutiliza a mesma chave para dedupe no relay.

## Evidência decisiva
Commit WordPress 484dad7d552e596110a55ca41d57813574c9174c substitui wp_generate_uuid4() no envio por chave HMAC determinística.

## Consequência
Preservar a configuração central e o relay MTProto existentes. Próximo teste de produção deve comprovar que duas submissões idênticas com a mesma chave resultam em um único envio remoto e que texto diferente gera novo envio.
