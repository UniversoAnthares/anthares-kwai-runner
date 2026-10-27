# Threads — recuperação de cinco transcrições ruidosas
STATUS: RUNNING
AREA: github
DATE: 2026-10-27
RUN: pending PR
JOB: 5 independent jobs
SUPERSEDES: test-hub/findings/2026-10-27-threads-asr-batch-149-running.md

## BASELINE_PROVEN
O workflow 40565169978 validou SHA de 149 mídias e produziu ASR small; PRs #1647 e #1650 integraram as provas e 144 metadados. Cinco clips permaneceram na quarentena por repetições no reconhecimento de fala: 1325, 2182, 4762, 7788, 11060.

## FAILED_AVOIDED
Não repetir o small com os mesmos parâmetros, não usar mídia como publicação real, não criar arquivos no PC e não liberar os cinco sem revisão da melhora objetiva.

## SUCCESS_SIGNAL
Uma reavaliação com configurações diferentes de segmentação e motor medium gera transcrição não repetitiva, com checksum e anexo WordPress correspondentes e cues preservados.

## FAILURE_SIGNAL
Voz não inteligível, repetições persistentes, divergência entre modelos, 429/quota, timeouts ou checksum diferente; preservar isolated.

## TEST_VALIDITY
Somente análise da saída small e medium, com conteúdo do áudio e taxa de repetição, poderá desbloquear metadados. Conclusão verde do workflow sozinha não basta.
