# Facebook Reels — correção editorial integrada
STATUS: PARTIAL
AREA: wordpress / cortes / facebook
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-wordpress/actions/runs/40724733696
JOB: none
COMMIT: https://github.com/UniversoAnthares/anthares-wordpress/commit/00a902248f2558718d2afe9d2b7d0dd922f0422c
SUPERSEDES: test-hub/findings/20261028-1218-lease-cortes-facebook-reels-editorial-gpt6.md

## Resultado
PR https://github.com/UniversoAnthares/anthares-wordpress/pull/206 integrada em main.
O publicador de Reels deixa de usar título/hashtags fixos de uma obra específica. Candidatos sem metadados editoriais validados são ignorados ANTES da reserva; candidatos válidos usam título e descrição canônicos do anexo. Upload binário, estados incertos e reconciliação preservados.

## Evidência decisiva
Branch head e SHA do arquivo após merge conferidos; texto fixo removido. Manifest premerge e sync/mirror do novo commit estavam em andamento ou na fila na última leitura.

## Consequência
Código principal corrigido. QA de manifesto, PHP lint e implantação efetiva Hostinger ainda dependem de evidência conclusiva; manter o item Facebook em PARTIAL até homologação. Não publicar vídeo real somente como teste e não reexecutar reservas incertas.
