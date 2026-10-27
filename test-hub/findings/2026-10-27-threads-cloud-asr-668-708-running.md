# Threads 668:708 — ASR externo com verificação de integridade
STATUS: RUNNING
AREA: github
DATE: 2026-10-27
RUN: none (pending pull_request)
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Transcrever somente o corte 668–708 do vídeo fOmihuHUT1M em runner efêmero GitHub Actions, sem gravar arquivos novos no PC e sem publicar em Threads.

## BASELINE_PROVEN
Neon mantém este corte queued/isolated com SHA-256 35cab02c13f525bbf1573cf91ce69bde2bde4b77fdf33856af415d96a7b6613a. A versão anterior da ferramenta gerava prova ASR local com faster-whisper-small, mas a regra vigente proíbe novos arquivos de trabalho no PC.

## FAILED_AVOIDED
Não usar D:\\ como staging; não criar execução social nem alterar flags de cloud primary; não repetir caminhos de autenticação Threads; não tentar download de artefatos pelo navegador pessoal.

## SUCCESS_SIGNAL
Log de job GitHub com ASR_VERIFIED e hash exato, anexo WordPress id verificado, cues não vazios, transcrição publicada como artifact GitHub privado.

## FAILURE_SIGNAL
Quota/limite, download de modelo indisponível, mídia e SHA divergentes, transcrição vazia, job inexistente ou falho. Não classificar como aprovado.

## TEST_VALIDITY
Prova válida somente se o job executou o SHA-256 do vídeo real e a transcrição do arquivo exato; sucesso do workflow sem sinal ASR_VERIFIED não basta.

## Segurança
Somente leitura de mídia pública. Sem secrets, sem Graph API, sem publicações, sem mutação Neon. timeout <= 15min; uma tentativa, sem repetição automática.
