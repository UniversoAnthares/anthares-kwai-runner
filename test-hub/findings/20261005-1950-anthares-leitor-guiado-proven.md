# Leitor guiado Anthares — implementação concluída
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: c4d5748d0e9315a7bd750ec7ec3f2f696aad62a7
SUPERSEDES: 20261005-1945-anthares-leitor-guiado-running.md

## Objetivo
Implementar no anthares-post-narrador os controles do leitor de referência, excluindo os dois últimos ícones.

## Resultado
Plugin elevado a 1.13.0. Estrutura de timeline adicionada ao PHP; JS ganhou cronômetro/progresso, seek aproximado e estado de player flutuante; CSS do Shadow DOM ganhou timeline e posicionamento flutuante. Play, pause, stop, velocidade, fallback nativo/neural e gate Anthares_PIX_Skills foram preservados.

## Evidência decisiva
Commits 6f017393d5ae5088669c20d45d59a690f40a2e1c, 509ff6e420e09341529c3221c31aea5828836325 e c4d5748d0e9315a7bd750ec7ec3f2f696aad62a7. Inspeção estática final confirmou version=1.13.0, timeline, :host(.is-playing), updateProgress, handler de seek e conto_narrador_elegivel.

## Consequência
A alteração está consolidada no repositório anthares-wordpress. Próxima validação útil é comportamento real no site após o mecanismo normal de deploy/sincronização do plugin.
