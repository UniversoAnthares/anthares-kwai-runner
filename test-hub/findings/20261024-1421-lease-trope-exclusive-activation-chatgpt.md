# Enciclopédia Narrativa — lease de ativação controlada do cron Neon exclusivo
STATUS: RUNNING
AREA: wordpress-enciclopedia
DATE: 2026-10-24
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/193
JOB: ency-item11-manual; Neon tropescron deployment #2
COMMIT: 11e622cd1407b770b64bf5df52e1eb588915788d (PR branch)
SUPERSEDES: test-hub/findings/20261024-1411-trope-exclusive-cron-partial-qa-safety-block.md
LEASE_START: 2026-10-24T18:21:00Z
LEASE_EXPIRES: 2026-10-24T18:48:00Z
OWNER: ChatGPT

## BASELINE_PROVEN
Preflight do titular PASS v6276158ef2239898; 594/594 QA manifesto na branch de PR; PHP 8.3 lint da mudança PASS; QA orchestrator PHP 8.3 no checkout main 4e46632e0db215931a3f0c29e8436f60ec145620 PASS todos os onze contratos; PR #193 muda só publicador e não afeta QA. Neon deployment #2 completed, TROPE_CRON_TOKEN listado sem revelar valor. Trigger único tropes-wpcron-15min ativo, HTTP 200 a cada 15 min no fallback. WordPress opção de segredo 64 caracteres, endpoint desabilitado 503, native publisher agendado.

## FAILED_AVOIDED
Falha de quota runner GitHub PR manifest; usar prova local manifesto e QA PHP autorizado, não repetir runner quota. Evitar cron duplo com guard aprovado antes de habilitação. Não expor segredo, não trocar o código antes do guard WP, não recriar trigger.

## SUCCESS_SIGNAL
PR #193 mesclada após verificação de HEAD e SHA. Plugin WordPress atualizado com backup/verify SHA e só seu cron nativo suprimido quando flag ativa. Neon função dedicada mantém env; um único trigger alterado no mesmo ID; execução real com status 200 no endpoint restrito; WordPress auth check sem token 403; marker anth_trope_last_neon_delivery_v1, heartbeat origin=neon_schedule, registro Neon correlacionados; rollback definido.

## FAILURE_SIGNAL
Drift concorrente, 403/503 quando auth correta, deploy da função falho, trigger duplicado, native job ativo no modo exclusivo, estado de publicação desconhecido, timeout sem reconciliação.

## TEST_VALIDITY
Comparar hashes, WP opção e source; só execução schedule Neon real vale, nunca chamada manual isolada. Conservar outros WP-Cron plugins e publicadores. Invalidar diagnóstico se baseline alterar em paralelo. Encerrar lease append-only.