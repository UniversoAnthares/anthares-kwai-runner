# CORTES: implantação da cadência proporcional 23h — Hostinger + Neon de produção

STATUS: PROVEN
AREA: wordpress-deploy / neon-functions-cortes / social-pacing
DATE: 2026-11-12
RUN: live-hostinger-ssh-and-neon-api
JOB: cortes-live-pacing-20261112
COMMIT: WordPress d72a71d59a67544ea1ce7aebf8cf3f71558f98a2; Neon source blob cb794dbc38c63b87a61213a86bced49f93525f27
SUPERSEDES: test-hub/findings/20261112-cortes-proportional-pacing-source-tested.md

## Evidência concreta de produção WordPress

Repositório: `UniversoAnthares/anthares-wordpress`, PRs #265 e #266 incorporadas no main. Arquivos transferidos pelo SSH autenticado já autorizado à hospedagem `anthares.us`, com staging fora de public_html, verificação de diff e backup `/home/u566597497/domains/anthares.us/.anthares-deploy-backups/cortes-pacing-d72a71d-20261112-r2`.

Arquivos substituídos com preservação da versão anterior:
- `cortes-control.php`: SHA256 `9463c9a675371d84b267a3c247df2355d9c9c2ab9014d00bbab98379aa7c9091`.
- `cortes-instagram.php`: SHA256 `942f2b90298812afb37803ea78de6ec6af9e3a0aa49ddb93e80b95bbc425cd3b`.
- `cortes-threads.php`: SHA256 `edbe35cd3b984aa96a8ff496870fa4694569659390babd5c9df2b837b0e4b118`.
- `cortes-facebook-cron.php`: SHA256 `03cf542b7ebc4465a432f1ba9da6010c2638bac57755f79b49c0fa3f42b31582`.
- `cortes-facebook-reels.php`: SHA256 `773f21354cb4c7c0ddaa0d99edb019e036e5a8dfe91071a7c5fc2be1a7e36cd4`.
- `cortes-destinations.php`: SHA256 `6bb02325bf345821ab3b2a274927dd8a106e89f969e62148352ae1b132a0fa72`.

O Hostinger devolveu `CORTES_PACING_HOSTINGER_DEPLOY=PROVEN`. Os seis arquivos passaram em `php -l` com PHP 8.2. O `wp plugin is-active anthares-clipper` retornou sucesso. Um teste somente-leitura executado no próprio WordPress real, por `wp eval-file`, validou os estados WAIT, DUE e BLOCKED_PLATFORM_LIMIT e devolveu `CORTES_PACING_HOSTINGER_WPCLI_QA=PASS`. Outro teste WP-CLI comprovou o carregamento de seis funções: núcleo `anthares_cortes_proportional_deadline`, segundo gate `anthares_cortes_pacing_assert_due`, Instagram, Threads, Facebook longos e Facebook Reels; devolveu `CORTES_PACING_ALL_WP_ROUTES_LOADED=PASS`.

## Evidência concreta de produção Neon

Projeto conectado `anthares-ara-ha` (`purple-flower-35918989`), branch principal `br-crimson-unit-b89nau08` — comprovadamente é o host `br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech`. O projeto estava acessível pela conexão Neon; o diagnóstico anterior de acesso ausente estava incorreto.

Foi usado o mesmo pacote ZIP sem dependências de `infra/neon-cortes-queue/index.mjs` aprovado no GitHub (blob SHA `cb794dbc38c63b87a61213a86bced49f93525f27`), contendo o gate `cortesDeadlinePacing`. Primeiro implantado em QA `br-silent-mud-b8fzvqta` (versão local 1, completed), com `GET ?action=health` indicando `ok:true`, `database_ok:true`. Em seguida implantado no principal como **deployment 66**, status `completed` e `active_deployment.id=66`, preservando as variáveis de ambiente existentes. `GET ?action=health` em produção devolveu `ok:true`, `database_ok:true`, `backend:neon-functions-cortes`.

A consulta SQL **somente leitura** no Neon de produção confirmou os campos reais para cálculo por conta: `target_key`, `status`, `publication_started_at`, `updated_at`, primeira e última publicação confirmada e fim local às 23h. Em 2026-11-12T15:42Z, Instagram: 255 queued / 31 used_today; Kwai: 23 queued / 4 used_today; LinkedIn pessoal: 278 queued / 11 used_today; LinkedIn empresa: 419 queued / 0 used_today; Pinterest: 220 queued / 0 used_today. São valores pontuais, jamais saldos permanentes.

## Segurança e limites

Nenhum teste de publicação/reenvio foi realizado. Tentativas `uncertain` continuam cercadas no ledger. O Instagram permanece sujeito à cota oficial da conta Meta; duplicar infraestrutura não reinicia esse limite. GH Actions `cortes-neon-ha-oidc-proof.yml` estava desabilitado e sua chamada de dispatch recebeu HTTP 422; o teste foi substituído por GET de saúde e SQL somente leitura da branch real, **sem alegar que o workflow OIDC foi homologado**.

## Limitações e próximas provas

STATUS de implantação Hostinger + Neon: PROVEN. Continua pendente acompanhar execuções públicas reais no horário calculado, a capacidade/cotas das APIs e confirmar implantação do cálculo em funções Neon independentes de TikTok/Threads ou em clientes físicos que não consumam o endpoint `cortesqueue` ou o plugin WordPress atualizado. Testes de fonte/CI não substituem recibos de publicação reais.

FAILURE_SIGNAL: endpoint health falha, funções WP-CLI desaparecem, divergência SHA, execução antecipada ou bloqueio após horário calculado. 
SUCCESS_SIGNAL: deploys 66 e WordPress ativo, testes sem publicação aprovados.
