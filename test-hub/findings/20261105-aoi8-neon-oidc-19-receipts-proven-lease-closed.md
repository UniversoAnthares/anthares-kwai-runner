# AOI #8 — recibo CI histórico autenticado e controlador Neon gratuito
STATUS: PARTIAL
AREA: github-ci/quota-successor-neon-oidc-controller
DATE: 2026-11-05
OBSERVED_UTC: 2026-11-05T02:52:05Z
ITEMS: [8]
LEASE: CLOSED
LEASE_OWNER: chatgpt-aoi8-20261105
SUPERSEDES: lease-20261105-aoi8-neon-oidc-exact-ci-receipt.md
GOVERNANCE_HASH: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
BASE_HEAD: f5ed84b0c13dc65d83b001b92da70a8c1c5edc87
COST: R$0, conta Neon free_v3, nenhum upgrade ou cobrança
PUB_OR_JOB_REPLAY: NONE

## Implementação e prova remota

Controlador alternativo **Neon Functions** implantado na conta gratuita já existente:
- Projeto: `purple-flower-35918989`, branch `br-crimson-unit-b89nau08`, função `cquotarec`, deployment #1 completed.
- URL: `https://br-crimson-unit-b89nau08-cquotarec.compute.c-14.us-east-1.aws.neon.tech/`.
- Fonte implantada versionada em `infra/neon-ci-quota-confirm/index.mjs` (6739 bytes; SHA256 `235b22e297423808707a8a76e5302c6152ebbb1428cba595f2c43d9464312407`; blob Git `a70a565ffd47964455a45ba3c6968cbc826713a8`). ZIP do deploy SHA256 `ee5b4a4ac77e6e37b40aae8dc307f55580bba858c61939b0ee21bd62d589b407`.
- `GET /` retornou HTTP 200 com `mode=exact_oidc_receipt_only`, `ready=true`; tentativa `POST /` sem token retornou HTTP 401.
- Implementado JWT OIDC GitHub RS256 com JWKS do emissor, validação estrita de aud/repo/workflow/ref/event/exp/iat, tupla única histórica e consulta autenticada à API Actions para conferir `run.id`, `path`, `completed/success`, `workflow_dispatch` e título com SHA.
- Atualização Neon via SQL condicional CAS `state=FALLBACK_SUBMITTED AND lease_generation=2`, dados imutáveis de origem e geração; proteção idempotente contra dupla confirmação. O endpoint somente confirma um resgate existente e aprovado. Nove testes isolados Node passaram (9/9).
- PRs operacionais: #2108 (controlador exato), #2109 (mock de tupla negativa), #2110 (isolamento de mocks dos dois testes legados). Todos integrados ao `main`.
- Primeiro smoke `41957079433` falhou no QA offline por 2 testes legados dependentes de DRY_RUN; **nenhum efeito em Neon**. Causa corrigida na PR #2110 antes de nova execução. Efeito controlado e reconciliado.
- Run `https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41957401745`, job `127015499390`, executou **nove testes Python (9/9 PASS)** e registrou `EXACT_RECONCILIATION_CONFIRMED_BY_OIDC_CONTROLLER`, status `completed/success`.
- Readback independente Neon `public.anthares_ci_quota_attempts`: **19/19 `FALLBACK_CONFIRMED`**, zero `FALLBACK_SUBMITTED`. O recibo `gitlab:87307248:3005500025` passou de geração 2 para geração 3, `successor_run_id=40942048873`, `receipt_confirmed=true`, preservando SHA original `94ba06e628d0b1ba0bdfeabbdfd9a00b86508759`.
- Workflow GitHub `gitlab-quota-watcher.yml` foi habilitado apenas para essa execução manual singular e depois restaurado `disabled_manually`, confirmado por consulta autenticada. Nenhum novo resgate, GitLab retry, publicação, workflow agendado ou execução PC foi iniciado.

## Limite e estado do item
A **pendência histórica de 19 recibos** está CONCLUÍDA. O item fixo #8 permanece PARCIAL enquanto a operação geral de cancelamento/failover depender do controlador Vercel HTTP 402 e dos demais adaptadores não homologados. A função Neon tem escopo exato desse recibo e não substitui reservas ou cancelamentos comuns. Forgejo continua HTTP 502 e mirror HTTP 503 em diagnóstico anterior. Falhas 401/403 e recusas de segurança continuam sem contorno.
