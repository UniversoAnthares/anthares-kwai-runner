# CORTES Threads — 149 comprovações editoriais concluídas
STATUS: PROVEN
AREA: github
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40565169978
JOB: 15 jobs, 149 clipes
COMMIT: c80d9914e68e94613ef9916bbdbd30f3127e1b6e
SUPERSEDES: test-hub/findings/2026-10-27-threads-asr-batch-149-running.md

## Resultado
O lote executou 15 jobs de transcrição de 149 mídias SHA-pinned do Neon, com 149 evidências ASR e nenhum erro de mídia. Provas arquivadas em main pela PR #1647.

Os metadados editoriais de 144 cortes foram validados, integrados na PR #1650 e suas quarentenas resolvidas de forma condicionada a SHA, status e razão.

Cinco clipes (inícios 1325, 2182, 4762, 7788, 11060) apresentaram reconhecimento ruidoso pelo modelo small. A execução independente https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40568800225 repetiu o processamento com small reconfigurado e medium, ambos sujeitos ao mesmo SHA original. O modelo medium forneceu cinco transcrições coerentes. A PR #1655 estendeu a aceitação de métodos apenas à variante medium comprovada, sem flexibilizar integridade/identidade, com teste de rejeição de método desconhecido e hash divergente. A PR #1659 integrou as cinco evidências editoriais. A PR temporária #1651 foi fechada sem merge.

## Evidência decisiva
Leitura de main confirmou 164 entradas no registro editorial: 15 existentes e 149 deste lote. Atualização SQL condicional no Neon retornou 144 + 5 registros resolved.
Estado final Neon: confirmed=131; queued=162; isolated=0; eligible=162; cloud_primary_enabled=false; in_flight=0.

## Consequência
A fila editorial foi totalmente liberada, porém **nenhuma das 162 publicações pendentes foi enviada**. Não ativar publicador cloud sem coordenação e fencing com o executor local; não reenviar mídias com submissão incerta nem executar lote experimental novamente.
