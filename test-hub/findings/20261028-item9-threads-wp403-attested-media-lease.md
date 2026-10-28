# Item 9 — Threads exact media lookup 403, prova atestada
STATUS: RUNNING
AREA: threads/cloud-media-exact-lookup
DATE: 2026-10-28
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40749020705
JOB: 123030392330
COMMIT: bdfdc6c5f9564247a5307a59b6a6a7b66dcc2414
OWNER: ChatGPT item 9
SUPERSEDES: none

BASELINE_PROVEN: GitHub job 123030392330 passou no OIDC/Bitwarden e nos testes mas falhou antes de publish com THREADS_EXACT_LOOKUP_FAILED WORDPRESS_HTTP_403 para threads:fOmihuHUT1M|g1:fOmihuHUT1M:3985:4025. Registry config/threads-verified-transcripts.json contém prova verificada para esse clip, incluindo SHA256, attachment_id, método ASR, texto e revisão. Threads QA #283 registrou redução de 121 a 104 itens pendentes, indicando atividade concorrente; Neon e idempotência precisam permanecer donos do estado real.
FAILED_AVOIDED: Não repetir execução falha sem alteração causal. Não contornar autenticação do WordPress; usar exclusivamente mídia pública pela URL canônica e somente quando a identidade exata estiver autorizada por atestado SHA-pinned, com hash real do arquivo verificado antes de qualquer claim.
SUCCESS_SIGNAL: testes unitários validam fallback exclusivamente para WP API HTTP 403 e somente identidade verificada, SHA de arquivo obrigatório, isolamento de outras falhas; GitHub Actions valida e publicação real apenas pelo fluxo primário cercado pelo Neon.
FAILURE_SIGNAL: Identidade sem evidência, SHA divergente, mídia inacessível, quota, lease ou autorização inválida; manter item em fila/quarentena sem reenvio incerto.
TEST_VALIDITY: NUNCA publicar como teste de código. Se houver execução concorrente, restringir a QA estático e comprovar publicações existentes por URLs/ledger. Não alterar gates, contas, segredos, limite diário ou sessões.
