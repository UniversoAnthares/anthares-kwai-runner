# 2026-10-07 — Auditoria de dependências externas para migração GitHub → GitLab

STATUS: PROVEN/PARTIAL
AREA: migration/github-to-gitlab/external-dependencies
DATE: 2026-10-07
RUN: manual-audit
COMMIT: main
SUPERSEDES: none

## Objetivo

Mapear os recursos externos que os sistemas Anthares realmente usam através do GitHub/GitHub Actions e verificar se podem continuar operando sob GitLab CI/CD.

## Conclusão

A infraestrutura externa do Anthares é, em sua maior parte, independente do GitHub e pode ser reutilizada pelo GitLab. O ponto que NÃO é uma simples troca de YAML é a camada de autenticação/controle que hoje identifica o executor como GitHub.

## Dependências externas mapeadas

1. WordPress/anthares.us
   - SSH para QA, avaliação WP-CLI, promoção de autofix e sincronização de alertas.
   - Credenciais atualmente referenciadas: ANTHARES_QA_SSH_KEY, ANTHARES_QA_SSH_HOST, ANTHARES_QA_SSH_USER, ANTHARES_QA_SSH_PORT.
   - Pode ser usado pelo GitLab CI via SSH sem alteração estrutural do servidor.

2. Cloudflare Workers / anthares-control
   - Deploy via Wrangler usando CLOUDFLARE_API_TOKEN.
   - Health checks HTTP públicos.
   - GitLab pode executar Wrangler e deployar Workers.
   - ATENÇÃO: anthares-control atualmente valida exclusivamente OIDC do GitHub: issuer token.actions.githubusercontent.com, claims repository/ref/workflow e executor=github.
   - Para migração real, implementar verificação OIDC do GitLab ou substituir por credencial específica de serviço. Também revisar rotas que fixam executor=github.

3. Render
   - render.yaml define o worker anthares-tiktok-render.
   - Segredos do serviço são ANTHARES_VIDEO_ENDPOINT, ANTHARES_VIDEO_SECRET, TIKTOK_STORAGE_STATE e RENDER_WORKER_TOKEN.
   - O serviço pode continuar independente do GitLab; Render suporta GitLab como provedor de código e também deploy via CI.

4. Hostinger / FTP
   - Clipper usa FTP/FTPS com FTP_HOST, FTP_USERNAME, FTP_PASSWORD, FTP_PORT, FTP_UPLOADS_ROOT e FTP_TLS.
   - GitLab CI pode executar o mesmo script Python/ftplib.

5. YouTube
   - Clipper usa YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN, YOUTUBE_COOKIES.
   - São credenciais da API/conta, não do GitHub. Podem ser armazenadas como variáveis protegidas do GitLab.

6. Meta / Instagram / Threads / X
   - social-api-publisher usa ANTHARES_VIDEO_ENDPOINT, ANTHARES_VIDEO_SECRET, META_GRAPH_VERSION, INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID, THREADS_ACCESS_TOKEN, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN e X_ACCESS_TOKEN_SECRET.
   - Nenhum desses serviços depende de GitHub. O GitLab pode fornecer as mesmas variáveis ao job.

7. Groq
   - Anthares Transcrição exige GROQ_API_KEY.
   - Anthares AI Hub possui provider Groq.
   - A integração é diretamente com api.groq.com e não depende do GitHub.

8. Telegram
   - Relay usa ANTHARES_TELEGRAM_RELAY_SECRET, ANTHARES_SESSION_ENCRYPTION_KEY, TELEGRAM_API_ID e TELEGRAM_API_HASH.
   - O relay é empacotado para Railway/Docker.
   - GitLab pode executar/deployar via CLI/CI; o Telegram não depende do GitHub.

9. Railway
   - anthares-telegram-relay possui railway.toml.
   - O deploy pode ser feito por Railway CLI em CI usando RAILWAY_TOKEN; não é intrinsecamente ligado ao GitHub.
   - Se o serviço Railway estiver atualmente conectado diretamente ao GitHub, essa conexão deverá ser trocada para deploy via CI/CLI ou outra fonte suportada.

10. Firebase Test Lab / Google Cloud
    - workflow firebase-testlab-secondary.yml usa GCP_SA_KEY, gcloud e Firebase Test Lab.
    - A infraestrutura de teste é independente do GitHub e pode ser chamada por qualquer CI que consiga instalar/configurar gcloud.

11. Forgejo / redundância
    - Existe sincronização para https://anthares.us/forgejo-sync.php.
    - O bootstrap atualmente baixa tools/bootstrap_forgejo_redundancy.sh de GitHub.
    - Após migração, essa referência deve apontar para GitLab ou para uma fonte neutra.

12. GitLab / Codeberg
    - O sistema já possui workflows de redundância para GitLab e Codeberg.
    - Hoje os workflows usam GitHub como origem principal.
    - Ao tornar GitLab primário, o sentido da redundância deve ser invertido/redefinido.

13. GitHub-specific
    - actions/checkout, setup-python, setup-php, upload-artifact e github-script.
    - schedules/workflow_dispatch.
    - GITHUB_* context variables.
    - GitHub Releases/Assets: o smoke de cortes baixa kwai-daily-current-021.mp4 de uma GitHub Release usando gh/GH_TOKEN.
    - GitHub Issues: o QA cria/fecha incidentes automaticamente via actions/github-script.
    - GitHub OIDC: usado para autenticar jobs no anthares-control.
    - Esses itens precisam ser substituídos, não apenas transportados.

## Particularidade crítica do Kwai/Android

O anthares-kwai-runner possui grande quantidade de workflows que executam Android/emuladores e verificações envolvendo /dev/kvm. O GitLab suporta runners Linux/Windows/macOS e runners próprios, mas não se deve presumir que um GitLab-hosted runner terá exatamente o mesmo ambiente KVM do GitHub.

Para equivalência operacional, a migração deve criar pelo menos um runner dedicado capaz de expor KVM/Android quando esses testes forem necessários. O runner deve ser isolado/efêmero e protegido porque alguns testes exigem capacidades privilegiadas.

## Equivalência final

- WordPress SSH: SIM
- Cloudflare deploy: SIM
- Cloudflare OIDC atual: NÃO sem alteração; requer adaptação
- Render: SIM
- Hostinger FTP: SIM
- YouTube: SIM
- Instagram/Threads/X: SIM
- Groq: SIM
- Telegram: SIM
- Railway: SIM via CLI/CI
- Firebase Test Lab: SIM
- Forgejo: SIM
- GitLab/Codeberg mirrors: SIM
- GitHub Releases/assets: SIM, migrando para GitLab Releases/artifacts ou storage neutro
- GitHub Issues: SIM, migrando para GitLab Issues/API
- GitHub Actions schedules/manual dispatch: SIM via GitLab pipelines/schedules
- GitHub OIDC claims hardcoded no anthares-control: NÃO sem alteração
- Android/KVM: SIM, mas exige runner adequado; não presumir equivalência com runner hospedado

## Bloqueio atual para autonomia do ChatGPT

A conexão disponível nesta sessão é com GitHub. Não há uma ferramenta/conector GitLab instalado nesta sessão que permita ao ChatGPT editar, criar commits, executar pipelines ou administrar projetos privados no GitLab da mesma forma.

Portanto, a migração técnica é viável, mas para preservar o modo de trabalho atual — ChatGPT editar código e atualizar sistemas sem intervenção manual — será necessário também disponibilizar uma integração operacional com GitLab.

## Fontes técnicas consultadas

- GitLab migration from GitHub / CI migration.
- GitLab OIDC ID tokens.
- GitLab CI/CD pipelines and runners.
- Cloudflare Workers GitLab CI/CD.
- Render Git provider documentation.
- Railway CLI/CI deployment.
- Firebase Test Lab CI documentation.

## Próximo passo

Não apagar nem desativar o GitHub. Fazer a migração em paralelo, começando por uma matriz GitHub → GitLab dos workflows e pelas dependências GitHub-specific acima. O anthares-control OIDC/executor e os workflows Android/KVM são os dois pontos que exigem engenharia real antes de declarar equivalência.
