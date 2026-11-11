# AOI-01 — prova de identidade de versão do Northflank antes de exigir credencial administrativa
STATUS: RUNNING
AREA: architecture/aoi01-northflank-existing-release
OWNER: chatgpt-aoi01-20261110-runtime-preflight
DATE_UTC: 2026-11-11
BASELINE_PROVEN: o workflow .github/workflows/northflank-tiktok-worker.yml tem SHA 6ad878ee90227ef8081b82956cd7e3d1c1e813d8 e exige NORTHFLANK_API_TOKEN / GET /projects antes de consultar /interactive-browser/revision; a auditoria externa teve HTTP 401 em 2026-11-10 (GitHub run 42869845569). O runtime responde /health HTTP 200, mas identity_verified=false e ready_for_tiktok=false; Forgejo Hostinger permanece HTTP 502. O peer GitLab 87307248 diverge e NÃO será sobrescrito.
FAILED_AVOIDED: não repetir implantação administrativa com token 401, não alterar Cloudflare/Neon/sessões, não habilitar publicadores, não substituir usuário do TikTok, não criar infraestrutura.
SUCCESS_SIGNAL: versão v12 atual e status autenticado podem ser aprovados sem acesso administrativo; versão divergente exige token válido para build; HTTP 401/403 do runtime falha sem contornar autorização; testes locais sem rede.
FAILURE_SIGNAL: qualquer chamada administrativa antes do probe runtime, tentativa de build sem token válido, duplicação ou acionamento de publicação.
TEST_VALIDITY: a alteração é apenas código, num workflow manual que permanece disabled_manually no GitHub; sua homologação produtiva exige evidência futura de versão/autenticação. Não confundir CI com implantação.
SOURCE: https://github.com/UniversoAnthares/anthares-kwai-runner/blob/main/.github/workflows/northflank-tiktok-worker.yml
COST_ADDED: 0
SOCIAL_PUBLICATIONS: 0
