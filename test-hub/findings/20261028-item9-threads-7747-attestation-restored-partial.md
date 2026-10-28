# Item 9 — restauração do atestado Threads 7747–7788
STATUS: PARTIAL
AREA: threads/cloud-media-exact-lookup
DATE: 2026-10-28
OWNER: ChatGPT item 9
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40785907390
JOB: 123158917480
COMMIT: 81eaefd6078883d9ae59377985a5342c7059f1dc
SUPERSEDES: test-hub/findings/20261028-item9-threads-7747-attestation-restore-lease.md

## Evidência causal
PR #1732 (merge 62c6a653) atestou o MP4 7747–7788; PR #1736 (merge a90fe0aa) eliminou as 75 linhas ao tratar migração Codeberg. O run 40785907390 (job 123158917480) morreu antes de publicar com WORDPRESS_403_EXACT_ATTESTATION_REQUIRED. GitHub e GitLab atuais omitiam esse corte.

## Reparo isolado comprovado
PR #1828 restaura exclusivamente a entrada original com attachment_id 17101, SHA256 da5a5166563a5677637e09460bb1cf87be5bcccb4bdc1eb4d280e541294db4a9 e atestado verificado. JSON parse OK; 165 entradas; igualdade exata de todas as 164 entradas preexistentes verificada; SHA do blob restaurado = 31365536d204a92dc827234a3d0bf5331eb6662c, idêntico ao commit original 62c6a653. Nenhum dado de fila, credencial, agendamento, quota, mídia ou executor foi modificado. Estado da intervenção: patch provado estaticamente; publicação real ainda exigirá próprio controle de hash/Neon e prova independente.

## Decisão
Lease deste reparo encerrado para mutações. Preservar deduplicação Neon e a rotina cloud primária. Não executar reenvio experimental. Aguardar validação CI/merge, e confirmar em ledger o sucesso de publicação sob versão integrada. Item fixo 9 permanece PARTIAL enquanto houver cortes aguardando confirmação.
