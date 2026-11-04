# WordPress Telegram — reparo da vinculação e do compartilhamento
STATUS: RUNNING
AREA: wordpress-telegram
DATE: 2026-11-03
RUN: none
JOB: ChatGPT — branch fix/telegram-share-20261103
COMMIT: none
SUPERSEDES: none

## Baseline
anthares-wordpress main 7b251bbab013b28b629e7ea93566e9e092e83ee3; anthares-telegram-relay main 8eefc5d373ad02e53a5684c78c61291d1f63a9f7. Railway /connect retorna Not Found na captura do usuário. O WordPress gera URL genérica na área do fórum e promete texto preparado no link do grupo sem garantia.

## Objetivo
Correção mínima em anthares-pix-sales/assets/telegram-usuario.{js,css} e includes/88-telegram-usuario.php; auditoria isolada do relay. Nenhum envio real, custo novo, alteração em editores/publicadores alheios ou deploy sem QA.

## FAILED_AVOIDED
Sem повторar envio com status incerto; nenhum fallback que simule publicação pessoal. Tratar serviço offline como offline.

## SUCCESS_SIGNAL
URL do tópico preservada, compartilhamento manual fiel, seção compacta e instruções curtas, tentativa de vínculo reprovada com erro claro em relay indisponível; QA sintático.

## FAILURE_SIGNAL
Quebra do fórum, modal inacessível, perda da desvinculação, status de envio falso.

## TEST_VALIDITY
QA estático prova contrato de código; validação em produção requer serviço saudável, implantação e conta de teste autorizada.

## Lease
Área wordpress-telegram, duração máxima 30 minutos a partir da criação, abrangendo somente arquivos explicitados. Encerrar por novo finding append-only.
