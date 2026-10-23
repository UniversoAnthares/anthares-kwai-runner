# Segunda passada — evidências adicionais da auditoria cross-repo
STATUS: PARTIAL
AREA: architecture, code, security, documentation, ci, assets
DATE: 2026-10-07
RUN: none (auditoria estática/local; sem publicação ou deploy real)
JOB: 370350d5e29b
COMMIT: none (resultados de clones multi-repositório; sem alteração remota de código)
SUPERSEDES: none
RELATED: 20261007-cross-repo-audit-followup.md; 20261007-cross-repo-audit-unresolved.md

## Objetivo
Registrar evidências específicas encontradas na segunda passada dos oito repositórios, complementar o follow-up mais recente e manter o histórico append-only. Não editar registros anteriores, não divulgar credenciais e não executar testes com contas/serviços reais.

## Resultado
A revisão encontrou falhas reproduzíveis de sintaxe/roteamento, segurança e configuração além das pendências resumidas no follow-up anterior. Correções pequenas foram aplicadas apenas em clones locais (Clipper, ZIP do relay, WordPress e Slideshow). Nenhuma foi implantada, commitada ou enviada por esta execução; PRs existentes têm alterações sobrepostas e não foram duplicados nem mesclados. O `anthares-kwai-runner` ficou somente leitura devido à regra de lease do próprio hub.

### Achados adicionais — `anthares-kwai-runner`
- `tests/test_control_publisher_integration_final.py:23-41` tem estrutura `try/except` fora dos `elif`; `python3 -m compileall -q .` e a execução direta falham com `SyntaxError` na linha 26.
- `kwai_queue_state.sh`/`kwai_reconcile_uncertain.sh` chamam `/github-queue/reconcile`, rota que `cloudflare-worker/src/index.js` não trata (404).
- Workflows do publisher TikTok montam JSON com quoting Bash inválido; o corpo expandido falha em `json.loads`.
- `kwai-direct-login-activity-matrix.yml` chama `kwai_direct_login_activity_probe.sh`, ausente do checkout; Bitrise aponta para `ci-hub/bitrise/runtime`, diretório inexistente.
- `kwai_claim_job.sh` copia resposta sem sanitizar CR/LF para `$GITHUB_ENV`; reprodução isolada demonstrou criação de uma variável extra.
- README descreve conteúdo/credenciais diferentes do Worker e publicadores atuais. ZIP de relay auxiliar tem formulário de 2FA na rota errada, permissões de volume Docker incompletas e `.pyc` empacotado.
- 28 scripts Bash, `node --check` e testes de promoção/runtime/email/IA passaram; `compileall` e teste final falharam por erro acima. Android/Docker/publicação real não foram executados. Nenhuma mutação foi feita por lease obrigatório.

### Achados adicionais — `anthares-clipper`
- Correções locais: hashing Python com `\\n` literal; `exit 39exit 34` no acceptance script; metas 33/66/100 e janela de agendamento incoerentes; teste de runner Android descartável; deadline de login de 720 s vs contrato de 120 s.
- Pendências: token em `SharedPreferences` em vez de Keystore; serviço Android não implementa o protocolo anunciado; worker Render aceita URL/redirects sem allowlist/bloqueio de IP privado (SSRF); cookies/estado TikTok podem ficar em plaintext; `.state/*.json` rastreados; README/lock de dependências ausentes ou incompletos. Fluxos com credenciais/publicação não foram testados.

### Achados adicionais — `anthares-telegram-relay`
- Quatro correções locais no `relay-source.zip`: rollback SQLite em colisões, validação de objeto JSON, permissões do diretório Docker e README de privacidade.
- Falhas restantes: reserva de `request_id` ocorre antes de enviar mensagem e pode mascarar falha como `duplicate`; clientes Telethon pendentes/expirados podem persistir; rate limit depende de forwarded headers e mantém chaves antigas; `PUBLIC_BASE_URL` não é lida; cobertura das rotas HTTP é insuficiente; ZIP inclui bytecode gerado.
- `unzip -t`, `compileall`, 3 testes unitários, `pip check` e smoke ASGI fictício passaram; não havia Docker para build e não houve acesso real ao Telegram.

### Achados adicionais — `anthares-transcricao`
- `/transcricao` não tem auth/quota/rate-limit; limite de 24 MiB só após download completo; erros/stderr do provedor retornam ao chamador; timeouts subprocesso+Groq excedem Gunicorn; dependências/imagem sem pin e container como root; faltam README, contrato, testes/CI.
- Testes mockados, `py_compile` e Gunicorn passaram. Groq/YouTube/Docker reais não foram usados.

### Achados adicionais — `anthares-wordpress`
- Duas URLs HTTP de CSS foram substituídas localmente pelo asset HTTPS/local existente; cinco READMEs de mídia foram corrigidos por listar arquivos presentes como ausentes.
- Pendências: OTP/2FA do ZIP relay envia formulários para rotas erradas; README do relay contradiz revogação real; Dockerfiles externo/interno esperam layouts diferentes; ZIP snapshot diverge em 41/105 entradas; PHPUnit não é executado pelo workflow; script SSH remoto baixa `main` sem pin/checksum; Plugin URI usa `example.com` placeholder.
- Lint/parse local: 326 PHP, 37 JS e 4 JSON sem falhas; não houve alteração de produção/pagamentos.

### `wiki`, `home` e `github-slideshow`
- `wiki` continua contendo apenas `README.md` placeholder, sem código/CI/assets; `home` tem árvore vazia no HEAD e clone raso sem o pai do commit que removeu o arquivo. Nenhum conteúdo foi inventado ou restaurado.
- Slideshow: reveal.js 3.9.2 recebe advisory XSS moderado GHSA-hhqj-cfjx-vj25; Bundler 1.17.3 falha em Ruby moderno e Nokogiri 1.11.1 falha no build; exclusões Jekyll apontavam ao diretório errado; CSS de impressão e plugins reveal não incluíam corretamente `site.baseurl`; opções reveal documentadas não chegam a `Reveal.initialize`; `script/stage` usa quoting Bash apesar de shebang POSIX.
- Correções locais em `_config.yml`, `_includes/head.html` e `_includes/script.html`; Jekyll/HTML Proofer local e `git diff --check` passaram. Nenhum fluxo de publicação foi executado.

## Logos e ativos visuais
Somente `anthares-wordpress` contém marca própria identificável: `wordmark.webp` 1209×315, `og-image.jpg` 1200×630 e backgrounds de dashboard; assinaturas de arquivo passaram e não houve corrupção óbvia. Nos outros repositórios não há logo/favicon/asset próprio; Slideshow contém apenas recursos upstream de reveal.js. Nenhuma marca foi criada ou alterada.

## Evidência decisiva
- Os relatórios locais completos estão em `/home/ubuntu/repos/audit-resumo-2026-10-07.md` e `audit-anthares-{kwai-runner,clipper,telegram-relay,transcricao,wordpress}.md`, além de `audit-wiki.md`, `audit-home.md` e `audit-github-slideshow.md`.
- Durante a revisão já existiam PRs com diffs sobrepostos: Clipper #37/#38, relay #1/#2, WordPress #15, Slideshow #2/#3/#5 e runner #1/#2/#3. Esta execução não criou PRs de código nem mesclou alterações para evitar duplicação.
- Limitações: sem Docker/Android/PHPUnit/Ruby legado em alguns ambientes; sem credenciais ou serviços reais; nenhuma operação em produção.

## Consequência
Manter a aceitação global como PARTIAL. Priorizar F-01/F-02/F-03/F-06 do runner e os riscos de SSRF/credenciais em Clipper/transcrição/relay; corrigir e validar localmente antes de merge/deploy. Não repetir teste com falha de sintaxe sem correção causal, não executar publicação real sem autorização específica e não mutar áreas serializadas do runner sem lease. Comparar PRs concorrentes antes de publicar patches, e manter findings append-only.
