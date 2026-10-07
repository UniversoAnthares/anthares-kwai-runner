# 2026-10-07 — Auditoria de dependências externas para migração GitHub → GitLab

STATUS: PROVEN/PARTIAL
AREA: migration/github-to-gitlab/external-dependencies
DATE: 2026-10-07
RUN: manual-audit
COMMIT: main
SUPERSEDES: none

## Objetivo

Mapear os recursos externos do Anthares que usam GitHub/GitHub Actions e verificar se podem continuar operando sob GitLab CI/CD.

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
    - O desenho futuro não deve assumir GitLab como autoridade única: a direção de sincronização deverá ser definida pelo roteador de provedores da fase 2.

13. GitHub-specific
    - actions/checkout, setup-python, setup-php, upload-artifact e github-script.
    - schedules/workflow_dispatch.
    - GITHUB_* context variables.
    - GitHub Releases/Assets: o smoke de cortes baixa kwai-daily-current-021.mp4 de uma GitHub Release usando gh/GH_TOKEN.
    - GitHub Issues: o QA cria/fecha incidentes automaticamente via actions/github-script.
    - GitHub OIDC: usado para autenticar jobs no anthares-control.
    - Esses itens precisam ser substituídos ou encapsulados pelo desenho de execução da fase 2.

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

## Estado da integração GitLab — atualizado em 2026-10-07

A sessão agora possui integração operacional com GitLab. O bloqueio anterior deste finding sobre inexistência de conector GitLab está superado.

O GitLab autenticado é `UniversoAnthares`. Existe atualmente um projeto importado:
- GitLab: `UniversoAnthares/anthares-kwai-runner`
- import_type: github
- import_status: finished
- origem: `https://github.com/UniversoAnthares/anthares-kwai-runner.git`

A importação NÃO está sincronizada com o GitHub:
- GitHub main: `3d1e4f55bfb6db974dfedb6ca7a77aa656a31b2b`
- GitLab main: `25b26ead0dafd848a293959541a73b27407db794`
- GitLab possui somente a branch `main` neste projeto no momento.

A integração de GitLab disponível nesta sessão permite leitura e alterações de arquivos/commits, mas não expõe uma operação de importação GitHub→GitLab nem uma operação de configuração de mirror remoto. Portanto, não foi feito um falso "sync" por reconstrução de arquivos: isso perderia histórico/refs e seria inadequado.

## Fase 1 — resultado desta rodada

STATUS: PARTIAL

Concluído:
- integração GitLab autenticada e operacional verificada;
- projetos GitLab existentes inventariados;
- projeto `anthares-kwai-runner` importado do GitHub confirmado;
- SHA, branch padrão e divergência GitHub/GitLab verificados;
- nenhum GitHub foi apagado, desativado ou promovido/demovido como autoridade;
- finding atualizado para não carregar a conclusão antiga de que não havia conector GitLab.

Não concluído nesta rodada:
- importação dos demais repositórios para GitLab;
- sincronização integral de histórico/branches/tags;
- configuração de mirror automático entre os dois provedores.

Esses pontos exigem uma operação de import/mirror que não está exposta pelo conector GitLab desta sessão. Não serão simulados por cópia parcial de arquivos.

## Fase 2 — desenho preliminar aprovado para estudo

A direção proposta é melhor do que declarar GitHub ou GitLab como autoridade única.

Os dois provedores devem ser tratados como **pares de execução/reposição**, enquanto a autoridade fica fora deles, no plano de controle. O `anthares-control` pode ser esse plano de controle, desde que passe a registrar:
- provider disponível;
- provider temporariamente bloqueado/sem quota;
- último commit conhecido em cada provider;
- operação em execução;
- lease de escrita/execução por repositório;
- checkpoint de sincronização antes do failover.

O roteador então escolhe GitHub ou GitLab conforme saúde/capacidade e, se o provider escolhido falhar antes da conclusão, faz failover para o outro somente depois de verificar o checkpoint.

Regra essencial: **não permitir dois escritores simultâneos para a mesma operação/branch**. Os dois podem permanecer com cópias equivalentes, mas a execução ativa deve ter um único lease por vez. Isso evita split-brain e concorrência.

A implementação desse roteador/failover NÃO foi feita nesta rodada.
