# CORTES — transição sem Buffer e publicadores diretos

STATUS: PARTIAL_PROVEN
AREA: queue
LEASE: test-hub/findings/lease-20261111-queue-direct-no-buffer.md
LEASE_STATE: CLOSED
DATE_UTC: 2026-11-12

## Produção e commits
- PR #2381, commit 3e4ca66500aab5e6569723f97fd6afa565fc8980: Buffer bloqueado nos quatro workflows de envio; prioridades de fonte recente implantadas em Instagram Graph direto, LinkedIn pessoal e Pinterest browser.
- Neon Function cortesqueue v61 implantada, substituída por v62 (completed/active) após a adição de LinkedIn organizacional.
- PR #2385, commit e0cad652d2faa7ff3266d751ae690a5a5d36bb6c: workflow Pinterest por navegador autenticado headless isolado; runtime também materializado sob D:\\AntharsWork\\cortes-pinterest-direct.
- PR #2387, commit f32e616da877f78c4c9975d23a85346c7d8f42df: validou a indentação YAML de concorrência no Instagram Graph e restabeleceu o workflow_dispatch.
- PR #2389, commit 52541f91df253efe8167fbf334c741585fdeafa8: LinkedIn organização oficial por OIDC e API REST, fila Neon fenced.
- PR #2394, commit bf7fafeab57240cbcee0115b8628f65c55fd5d6a: ativação após push.
- PR #2396, commit 1cc558f6f43f5d290946a802c3da678abf4e98de: admite verbos company-* no cliente Neon.
- PR #2397, commit 48de2363525293bee5d88943a5ad4a56fe29aa77: tenta OAuth corporativo dedicado; indisponível. Fallback de token pessoal não autoriza criação na organização e ficou preso em UNCERTAIN, sem replay.

## Publicações efetivas (snapshots desta rodada)
- Fonte cOhqEaY3-08 Instagram Graph: 6 CONFIRMED e 22 QUEUED, 1 STARTED observado às 03:34 UTC em 12/11; execução oficial #43147631904 confirmou URL https://www.instagram.com/reel/DfoFBgpts-F/.
- LinkedIn pessoal: 2 CONFIRMED, 13 QUEUED. Primeiro aceite oficial em #43146739790, conciliação pública efetuada.
- Pinterest: Chrome headless real iniciado com ARA remote_job_start. Bloqueio de login do perfil exclusivo AntharesPinterest, indicador PINTEREST_BROWSER_LOGIN_REQUIRED; sem novo Pin.
- LinkedIn organização: código e Neon v62 ativos; 29 cortes ainda queued e pelo menos 1 quarantine UNCERTAIN. Credencial oficial da organização não existe nos segredos disponíveis à execução; fallback de BWS CLI falhou antes de alterar fila. Nenhum comprovante público da conta organização.
- Kwai hosted: #43146759535 parou antes de Android porque cofre retornou KWAI_PRIVATE_VAULT_SESSION_ABSENT=1; nenhuma postagem falsa/duplicada.

## Segurança e conclusão
- Buffer removido das rotas de envio.
- Preservados media_url, IDs, fingerprint, lease generation e jobs uncertain; nenhum repost cego.
- Áreas abertas: OAuth corporativo LinkedIn, login dedicado Pinterest, vault Kwai, publicações futuras nas filas.
