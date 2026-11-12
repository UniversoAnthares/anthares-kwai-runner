# Vercel Hobby quota — lease de reordenação segura
STATUS: RUNNING
AREA: vercel/quota-routing
DATE: 2026-11-12
OWNER: chatgpt-gpt6-20261112-vercel-quota
LEASE: ACTIVE_IN_BRANCH
BASE_SHA: d17d8b6dbfb417b2f01039b1156d8cd41164fb7d
BASELINE_PROVEN: Vercel Hobby Usage autenticado indica deployments pausados por Fluid Active CPU desde 2026-10-29 até 2026-11-28; AOI #8 já possui controlador Neon/OIDC para recibos de CI e ARA Cloudflare/Neon como contingência de compute.
FAILED_AVOIDED: repetição de endpoint Vercel HTTP402, cobrança, nova publicação, troca cega de owner e criação de segundo escritor.
SUCCESS_SIGNAL: regras de seleção movem quota_scope bloqueado ao fim e o excluem do despacho; recepção de configuração versionada, testes locais do helper e PR disponível.
FAILURE_SIGNAL: qualquer substituto sem mesma função, quota independente, recibo/fencing, sucesso do contrato ou falta de autorização de mudança de owner.
TEST_VALIDITY: alterações só de fonte/roteamento preventivo; nenhum deployment ou publicação; validação de sintaxe e invariantes sem efeito externo.
SCOPE: ci-hub/quota-status.json; ci-hub/executor-routing.json; tools/ci_quota_cancel_first.py; tests/test_ci_quota_cancel_first.py.
