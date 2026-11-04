# AOI 21 / Kwai — reconciliação pública insuficiente; atestação criptográfica QA passou
STATUS: PARTIAL
AREA: kwai-uncertain-reconciliation/independent-readback-qa
DATE: 2026-11-04
OBSERVED_UTC: 2026-11-04T14:40:55.650Z
RUN: node-v22-isolated-sandbox, no workflow dispatched
JOB: none
COMMIT: 09d246739bca9ec652fbba93574d2b3ccfd447be
SUPERSEDES: 20261104-lease-kwai-68-public-proof-hmac-qa.md
LEASE_OWNER: chatgpt-reestruturacao-cortes-20261104
LEASE_AREA: kwai-uncertain-reconciliation/independent-readback-qa
LEASE: CLOSED
GOVERNANCE_MANIFEST: 223433740e807a90
ITEMS: [21]
COST_ADDED: 0

## Nova observação direta
- Neon SELECT somente leitura com alvo exato kwai:lucasrosalem: 456 confirmed e 68 uncertain; nenhum outro estado entre queued/leased/started. ZERO registros alterados.
- TinyFish Search gratuito por publicações do handle @lucasrosalem retornou zero URLs de vídeos; TinyFish Fetch gratuito no perfil https://www.kwai.com/@lucasrosalem confirmou perfil canônico e descrição anthares.us, porém só forneceu links gerais da plataforma, nenhum link /photo/ID ou share URL. Ausência de resultados não comprova que posts não existem.
- TinyFish Wallet observada com saldo negativo, portanto nenhuma sessão de automação paga foi iniciada. Anthares Browser Hub local foi consultado apenas em modo status, sem novos processos e sem abrir sessões pessoais.

## QA independente de assinatura sem publicações
- PR #2057 em draft: `infra/neon-cortes-queue/index.mjs` blob `e3fe38816aa5f478b4ba40fbec09efc68708ea5c`; `tests/cortes_kwai_independent_attestation.test.mjs` blob `2697776682ab2d662b49cff9c7350df6bb2aa55a`.
- Um trecho da validação de `kwai-confirm` foi reproduzido em teste isolado Node.js v22.16.0 com crypto.createHmac e crypto.timingSafeEqual **reais**, mock SQL, segredo exclusivamente sintético, nenhuma rede. Teste local SHA256 `a516815b596df3b2b4f71b8723f8de92872eca7152808d3a4a1f41c2645a08c6`.
- Node `--test`: 7/7 PASS: URL incorreta, ausência de chave, HMAC errado, evidência vencida, geração alterada, assinatura correta chegando apenas ao SQL mock com fencing/HMAC removido, conta divergente.
- Limite explícito: teste do trecho reconstruído, **não** execução byte a byte do módulo original, **não** execução do teste original do repositório, e **não** integração Neon/Kwai.

## Resultado / bloqueios
- 68 de 68 permanecem RECONCILE_REQUIRED: nenhum ID/URL e atestação externa independente correspondeu a um post específico. Proibido marcar confirmed, closed_unverified ou retry automático sem prova correspondente.
- PR #2057 fica DRAFT, publicação flag OFF; PR privada Clipper #229 de CAS/fencing continua intacta. O verificador independente real da conta Kwai ainda falta ser homologado e autorizado.
- Próximo passo: receber URLs+IDs públicos verificáveis por post e vincular às mídias originais com prova independente; então efetuar reconciliação sob owner/lease e idempotência sem republicar. Alternativamente validar uma sessão Kwai remota já autenticada em ambiente aprovado, após quota e segurança.
- Custo adicional zero, nenhum dado de produção alterado. Rollback: documentação apenas por revert SHA.
