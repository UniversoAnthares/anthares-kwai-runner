# AOI #16 — importação do retry longo corrigida; lease encerrada
STATUS: PARTIAL; SOURCE_FIX_MERGED; LEASE_CLOSED
AREA: qa-p0-cortes-long-retry-module-import
DATE_UTC: 2026-11-09T01:41:29.809Z
ITEMS: [16]
SUPERSEDES: lease-20261109-aoi16-cortes-long-retry-import.md
OWNER: chatgpt-aoi16-cortes-long-retry-20261109

## Resultado causal
Runs originais Clipper 39881056747 e 41064244203 pararam antes do processamento em ModuleNotFoundError: cortes_source_adapter quando qa/cortes_long_retry_guard.py era executado diretamente.
Clipper PR #241 incorporada com SHA d5e830222691e106dda64e481023fb5c34bedb05. Patch mínimo adiciona raiz do repositório ao sys.path exclusivamente em execução direta, sem mudar lógica do admit.
Teste isolado fora do PC do titular: DIRECT_IMPORT_PASS, código de saída 0; simulação com módulo raiz, sem contato com WordPress/Neon.
PRODUCTION_PROVEN: NO; execução do workflow legado self-hosted desativada não foi reativada.
ISSUES: #1145, #1982 permanecem abertos até aceite causal operacional.
EFFECTS: mídia=0; envios=0; filas=0; scheduler=0; credenciais=0; custo adicional=0.
Rollback: reversão do commit de código via PR, preservando todos os registros.
