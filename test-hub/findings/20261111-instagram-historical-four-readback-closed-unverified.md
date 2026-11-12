# Instagram — four historical Buffer records: exhaustive exact-link readback

STATUS: PARTIAL
AREA: instagram
DATE: 2026-11-11
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43148066349
JOB: 130950490391
COMMIT: ec7ae73cc339ffba6e75bac9970bfddac1e2f855
SUPERSEDES: none

## Objetivo
Resolver a incerteza histórica de quatro entregas Instagram de outubro,
preservando a identidade do master, do destino e qualquer publicação antiga.

## Resultado verificado
O script existente `tools/cortes_buffer_orphan_readback.py` examinou 200 posts
do canal Buffer Instagram exato, percorrendo toda a janela histórica esperada.
Resultado: `historical_window_complete=true`, `exact_matches=0`,
`unmatched=4`, `no_posts_created=true`.

Referências curtas dos quatro registros:
- `11fe6e0c39d7`: zero correspondências exatas.
- `293808e7fe0a`: zero correspondências exatas.
- `4b66a3e5d3b4`: zero correspondências exatas.
- `c652b35312dd`: zero correspondências exatas.

## Disposição administrativa
**CLOSED_UNVERIFIED** para a investigação histórica do Buffer: nenhum recibo
permite confirmar publicação desses quatro registros, e nenhum deles deve ser
reenviado automaticamente. O ledger Neon preserva estados `uncertain` até
uma atualização transacional autorizada de reconciliação/encerramento; esta
nota não altera o ledger nem representa publicação confirmada.

## Evidência decisiva
Logs da execução acima: quatro eventos `CORTES_LEGACY_BUFFER_EXACT_MATCH`
com `post_count=0`; evento `CORTES_LEGACY_BUFFER_CENSUS` com
`posts_scanned=200`, `historical_window_complete=true` e
`exact_matches=0`.

## Consequência obrigatória
Preservar `master_id`, checksum, publicação incerta e regras de retenção.
Reabrir apenas perante ID/link externo verificável com conta compatível.
Não reciclar essas quatro tentativas em nenhuma rota Graph/Buffer alternativa
sem prova remota de ausência e transição explícita e autorizada no Neon.
