# Leitor guiado Anthares — implementação
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Atualizar anthares-post-narrador para reproduzir os controles observados no leitor de referência: pausa/continuar, parar, tempo atual/duração, velocidade, acompanhamento visual do trecho narrado, barra navegável de progresso e player flutuante durante reprodução, excluindo os dois últimos ícones da referência.

## BASELINE_PROVEN
anthares-post-narrador 1.12.5 no branch main de UniversoAnthares/anthares-wordpress, com player compartilhado entre posts e contos, Web Speech fallback e controles existentes de play/pause/stop/rate.

## FAILED_AVOIDED
Evitar substituir a autorização de contos, o fallback neural/nativo e a estrutura compartilhada já existentes. Alteração limitada ao player e à instrumentação de progresso.

## SUCCESS_SIGNAL
Arquivos do plugin atualizados no GitHub; PHP expõe controles de tempo/progresso; JS controla progresso, seek aproximado e destaque do trecho; CSS mantém player flutuante durante reprodução.

## FAILURE_SIGNAL
Erro de sintaxe, perda dos controles existentes ou quebra do gate de contos.

## TEST_VALIDITY
Inspeção estática dos arquivos atualizados deve encontrar os novos data-attributes e handlers sem remover os caminhos existentes de autorização e fallback.
