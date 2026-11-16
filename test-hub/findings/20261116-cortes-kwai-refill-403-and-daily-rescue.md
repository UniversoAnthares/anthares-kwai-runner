# CORTES Kwai: repositor 403, rotina diária ausente e recuperação

STATUS: PARTIAL
AREA: kwai|github|wordpress
DATE: 2026-11-16
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/43917516014
JOB: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/43919766676
COMMIT: 236514e6b0e9a741a6584e4096dd3404642e4882
SUPERSEDES: none

## Diagnóstico
Em 16/11 até 13h local, o schedule diário do Clipper (06h40 local, cron 10:40 UTC) não havia disparado. O schedule anterior ocorreu em 15/11 e reportou success com curtos `new_processed=0`. O último refill Kwai com sucesso era de 13/11; os de 14/11 e 15/11 falharam. No run 43749455978, a leitura WordPress por `urllib` falhou com HTTP 403. O `cortes_source_adapter.py`, com `requests`, autenticou e leu o mesmo WordPress no diagnóstico 43916068368 de 16/11. A fila Neon `kwai:lucasrosalem` tinha pending=0, confirmed_today=0 e 623 confirmações históricas.

## Correções implantadas em anthares-clipper/main
- 47ccbeca880b9a13381da04783ec2825ee7b1c56: instala `requests` no refill hospedado.
- 236514e6b0e9a741a6584e4096dd3404642e4882: HTTP autenticado WordPress via `requests`, retries limitados a GET transitório e POST sem reexecução ambígua.
- 9b38c3d00776f1ac3c303b06d381314428a04945: cron horário de refill limitado a 12 por tentativa, 06h17 a 22h17 locais; quota e deduplicação no Neon/WordPress.
- cabfbb8b92b26bb1b391fbc69580c3628fe3a8fa e 8214b0e909a40869969cd39eb7e8686696fda309: acerta janela de 10:40 UTC e busca específica do workflow diário; recuperação apenas do inventário/lock (sem produção de mídia).
- 647fb799f4888c87d9704c44436b31ca0255e798: rescue do cron em Ubuntu hospedado nos horários 07h15, 08h15, 10h15 e 14h15 locais. Habilitado. Run 43918966391 passou e não duplicou o workflow diário ativo.

## Comprovação
Run 43917516014 (reserve=1) enfileirou um master. Android físico preservou/verificou SHA, recebeu recibo de publicação, e recuperação de prova pública confirmou `KWAI_PUBLIC_VIDEO_PROVEN` e `ACK_REPAIRED_COMPLETE` às 13h32 locais. WordPress callback retornou `completed`. URL: https://www.kwai.com/@lucasrosalem/video/5208844556818334962. Neon: `confirmed_today=1`, total confirmado 624. Run 43919766676 terminou success e enfileirou mais 12, sem duplicidade; Neon em 13h38 tinha pending=12, status WAIT. O workflow diário 43918950439 iniciou por outro executor às 13h29 locais, com source e long completos e short em curso na última leitura. Ele não foi reexecutado por esta auditoria.

## Pendências e restrições
Rever o resultado final do produtor 43918950439 e progresso real (o status geral success anterior ocultou zero vídeos novos). Confirmar um futuro `schedule` horário efetivo e um resgate verdadeiro quando faltar a execução matinal; o teste cobriu bloqueio seguro quando havia daily ativo. Postagens `started` ou `uncertain` requerem prova de URL, conta e mídia antes do ACK. Sem reenvio cego, troca de conta, deleção ou alteração de espelho GitLab. Código de produção alterado somente no GitHub canônico.
