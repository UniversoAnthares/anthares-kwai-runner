# Varredura total cross-repo e integração GitLab — follow-up

STATUS: PARTIAL / BLOCKED
AREA: cross-repo-audit/gitlab/failover
DATE: 2026-10-07
RUN: sandbox-full-scan

## Escopo

Oito `origin/main` foram atualizados e auditados: `anthares-kwai-runner`, `anthares-clipper`, `anthares-telegram-relay`, `anthares-transcricao`, `anthares-wordpress`, `wiki`, `home` e `github-slideshow`. Foram verificados código, documentação, workflows, `.gitlab-ci.yml`, logs/resultados, padrões de segredo, artefatos e caches. Foram executadas validações Python, Bash, JSON, JavaScript, PHP, testes do relay, provider router e `npm audit`.

## Falhas confirmadas

1. `anthares-kwai-runner` `main` em `b91d811` não compila integralmente: `tests/test_control_publisher_integration_final.py:26` contém um `elif` depois de um `try/except` fora da cadeia, produzindo `SyntaxError`. O provider router isolado passa, mas o teste de contrato não.

2. Os workflows ativos de mirror de `anthares-kwai-runner` e `anthares-wordpress` falharam porque `GITLAB_MIRROR_URL` chegou vazio ao runner. Runs observados: [Kwai #37696590120](https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37696590120) e [WordPress #37696525982](https://github.com/UniversoAnthares/anthares-wordpress/actions/runs/37696525982). O workflow permanece fail-closed corretamente; falta provisionar a URL/Deploy Token fora do repositório e confirmar igualdade do SHA de `main`.

3. O workload GitLab do Clipper ainda é somente código/importação. O finding de workload real registra ausência das variáveis protegidas `WP_SITE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` e `YOUTUBE_REFRESH_TOKEN`, impedindo publicação completa.

4. A migração não é ainda failover simétrico: há dependências de GitHub Actions, GitHub Releases/Assets, GitHub Issues, claims OIDC do GitHub e GitHub como origem padrão. Kwai/Android ainda exige runner dedicado com KVM/ADB/emulador.

5. `anthares-transcricao` versiona `__pycache__/app.cpython-312.pyc`; remover do Git e impedir reincidência via `.gitignore`.

6. `github-slideshow` usa `reveal.js` 3.9.2. `npm audit` confirmou XSS moderado `GHSA-hhqj-cfjx-vj25`, corrigido a partir de 4.3.0; atualizar e testar compatibilidade.

7. O conector `GitLab API` está habilitado na configuração da sessão, mas a credencial está encapsulada e o navegador desta execução redireciona para login. A auditoria não deve declarar que todos os projetos/variáveis/pipelines GitLab foram verificados diretamente sem uma sessão GitLab autenticada disponível.

## Pendências de operação

O mirror precisa ser ativado com secret externo; as variáveis de runtime precisam ser cadastradas no projeto GitLab; Cloudflare/OIDC, Docker, WordPress/FTPS/YouTube, TikTok/Kwai, Groq, Railway e Android/KVM precisam de seus ambientes reais; e os PRs sobrepostos/governança dos repositórios ainda precisam de decisão do mantenedor.

## Segurança

Nenhum token, senha, cookie ou valor de secret foi gravado neste finding.
