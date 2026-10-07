# Auditoria cross-repo e execução de correções — Anthares
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-07
RUN: none
JOB: MDE9nE00YIndrW2UFftCo3
COMMIT: pending
SUPERSEDES: none

## Objetivo
Auditar os oito repositórios acessíveis à conta GitHub `UniversoAnthares`, cobrindo documentação, código, workflows, testes e logos/branding; aplicar correções locais de alta confiança; registrar neste finding tudo que falhou, ficou bloqueado ou depende de decisão/ambiente externo.

## Escopo auditado

- `anthares-kwai-runner` — 925 arquivos versionados.
- `anthares-clipper` — 198 arquivos versionados.
- `anthares-telegram-relay` — `Dockerfile` + `relay-source.zip`.
- `anthares-transcricao` — 4 arquivos originais, agora com documentação/testes/CI adicionados localmente.
- `anthares-wordpress` — 565 arquivos versionados.
- `wiki` — 1 README no snapshot inicial.
- `home` — HEAD vazio.
- `github-slideshow` — 140 arquivos, incluindo reveal.js vendorizado.

Relatórios detalhados: `/home/ubuntu/github-audit/reports/cross-repo-audit.md`, `01-anthares-kwai-runner.md`, `02-anthares-clipper.md`, `03-anthares-telegram-relay.md`, `04-anthares-transcricao.md`, `05-anthares-wordpress.md`, `06-wiki.md`, `07-home.md` e `08-github-slideshow.md`.

## Falhas e lacunas completas por repositório

### `anthares-kwai-runner`

1. JSON inválido por quoting shell em workflows TikTok — **CORRIGIDO LOCALMENTE**.
2. Workflow referencia `kwai_direct_login_activity_probe.sh` inexistente — **ABERTO**.
3. `tests/test_control_publisher_integration_final.py` não compilava — **CORRIGIDO LOCALMENTE**.
4. Token Instagram/Threads em query string — **CORRIGIDO LOCALMENTE**.
5. Fila de e-mail não implementa o contrato documentado de `Delivery` — **ABERTO**.
6. Failover Git usa sincronização potencialmente destrutiva antes da verificação — **BLOQUEADO** por acesso/política de provedores.
7. Verificador de provedores só compara uma branch, não tags — **ABERTO** por decisão de refs protegidas.
8. Android Agent não possui logo/ícone rastreado — **BLOQUEADO** por asset oficial.

### `anthares-clipper`

1. `tiktok_web_publish_local.py` tinha SyntaxError — **CORRIGIDO LOCALMENTE**.
2. Cadência efetiva de 3–6h contradiz contrato/teste de 61–300s e meta — **BLOQUEADO** por decisão de produto; o hub registra que modo diagnóstico 3/dia e produção 100/dia são distintos.
3. Token Android em SharedPreferences, não Keystore — **BLOQUEADO** por estratégia de migração/release.
4. Identidade TikTok divergente entre Render e GitHub Actions — **BLOQUEADO** por decisão/credencial canônica.
5. Bootstrap Waydroid mascarava falha — **CORRIGIDO LOCALMENTE** removendo `|| true`.
6. Teste de arquitetura exigia cache incompatível com AVD descartável — **CORRIGIDO LOCALMENTE** alinhando o teste à política sem cache.
7. Janela de login de 720s excedia o timeout do workflow e falhava o contrato de 120s — **CORRIGIDO LOCALMENTE**.
8. Branding mistura Lucas Rosalem/Anthares e não há logo rastreado — **BLOQUEADO** por decisão e asset oficial.
9. `.gitignore` contradiz estado `.state` rastreado — **ABERTO** para decisão de persistência.
10. README não documenta exceções OIDC — **ABERTO** para revisão do contrato de claims/sensibilidade.

### `anthares-telegram-relay`

1. Reserva de `request_id` antes do envio transforma falha em falso duplicate/sucesso — **ABERTO**.
2. Falha transitória no callback elimina vínculo pending — **ABERTO**.
3. Envelope HTTP real usa `detail` e diverge do README — **ABERTO** por contrato do consumidor.
4. `/connect` aceita iniciação pública sem nonce/assinatura — **BLOQUEADO** por decisão de autenticação/quota.
5. Rate limit confia em forwarded headers e cresce sem expiração global — **BLOQUEADO** por definição de proxy confiável/topologia.
6. Dockerfiles raiz e interno divergem na preparação do volume — **ABERTO**; CI de integridade do ZIP foi adicionado localmente.
7. `PUBLIC_BASE_URL` documentada mas não consumida — **ABERTO** por decisão de contrato.
8. README referencia `TELEGRAM-MTPROTO-RELAY.md` ausente — **ABERTO**.
9. Não havia CI nem testes de rotas/build — **CI ADICIONADA LOCALMENTE** para validar ZIP, compile e testes existentes.
10. Segredo HMAC não é validado contra mínimo documentado — **ABERTO** por política de startup/compatibilidade.

### `anthares-transcricao`

1. Cookies YouTube continuam alcançáveis no histórico Git — **BLOQUEADO**: exige revogação de sessões e saneamento coordenado de refs; nenhum valor foi exposto.
2. Endpoint anônimo permite abuso de downloader, disco, rede e cota Groq — **ABERTO/BLOQUEADO** por decisão de autenticação, quota e gateway.
3. Respostas refletiam stderr/corpo upstream — **CORRIGIDO LOCALMENTE** com mensagens genéricas e logs server-side.
4. Build não reprodutível/container root — **PARCIALMENTE CORRIGIDO LOCALMENTE**: container agora usa usuário não-root; pinagem de versões permanece aberta.
5. Não havia documentação operacional — **README ADICIONADO LOCALMENTE**.
6. Não havia testes/CI — **TESTES E CI ADICIONADOS LOCALMENTE**; sem chamadas reais a YouTube/Groq.

### `anthares-wordpress`

1. Cópia executável do File Bridge sem allowlist — **BLOQUEADO** por confirmação do pacote/plugin ativo em produção; não foi removida.
2. Vídeos `mapa.webm`/`mapa.mp4` ausentes — **BLOQUEADO** por falta de assets oficiais/fallback aprovado.
3. Spool TikTok sem limpeza/replay/retention — **ABERTO** por política de recuperação.
4. README declara Kwai, worker implementa apenas TikTok — **BLOQUEADO** por decisão de escopo/credenciais.
5. Worker sem lockfile/workflow versionado — **ABERTO** por decisão de runner/release.
6. Versões README/plugin/worker divergentes — **ABERTO** por escolha de fonte canônica.

### `wiki`

1. README efetivamente vazio — **CORRIGIDO LOCALMENTE** com escopo e estado placeholder.
2. Sem lint/link-check versionado — **ABERTO** até haver conteúdo real.
3. Sem branding/assets — **CONDICIONAL/BLOQUEADO** por requisito de marca não comprovado.

### `home`

1. HEAD não contém artefatos do projeto — **BLOQUEADO**: não há fonte para restaurar.
2. Bootstrap histórico apontava para classes ausentes — **BLOQUEADO** junto com a ausência de fonte.
3. Sem docs, testes, CI/configuração/assets — **ABERTO/BLOQUEADO** até decisão de arquivar ou recuperar o projeto.

### `github-slideshow`

1. `script/stage` apontava por padrão para `caption-this` e usava `--force` — **CORRIGIDO LOCALMENTE**: destino passou a ser explícito e push não-forçado.
2. Staging anunciava sucesso após falhas — **CORRIGIDO LOCALMENTE** com `set -eu`, limpeza e validação de etapas.
3. CSS PDF apontava para caminho inexistente — **CORRIGIDO LOCALMENTE**.
4. Exclusões Jekyll usavam árvore antiga — **CORRIGIDO LOCALMENTE**.
5. Lockfile sem `package.json` — **CORRIGIDO LOCALMENTE** adicionando manifesto; `npm ci --offline` permaneceu não conclusivo porque o tarball não estava no cache do sandbox.
6. `script/stage` misturava `/bin/sh` com sintaxe Bash — **CORRIGIDO LOCALMENTE** com sintaxe POSIX.
7. Sem testes/CI próprios — **ABERTO**; Ruby/Bundler ausentes no sandbox.

## Correções locais verificadas

- `anthares-clipper`: `py_compile`, teste de arquitetura e `bash -n` — **PASS**.
- `anthares-kwai-runner`: testes sociais, teste de integração corrigido, `py_compile`, 12 blocos shell dos workflows TikTok e JSON sintético — **PASS**.
- `anthares-telegram-relay`: `unzip -t`, `zipfile -t`, compile e 3 testes existentes — **PASS**.
- `anthares-transcricao`: 5 testes mockados, `py_compile` e redaction de falhas upstream — **PASS**.
- `github-slideshow`: `sh -n` e existência de assets PDF/paper — **PASS**; instalação offline ficou limitada ao cache.
- Todos os diffs locais: `git diff --check` — **PASS**; busca de segredos novos nos diffs — **PASS**.

## Consequência

Não repetir testes ou estratégias marcados como BLOQUEADO/ABERTO sem mudança causal explícita. Não executar publicação, login, deploy, force-push, revogação de cookies, saneamento de histórico, alteração de produção, migração Android ou escolha de identidade/cadência apenas com base nesta auditoria. Os patches locais devem passar por revisão normal antes de serem publicados.
