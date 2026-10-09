# WordPress QA multi-IA, Copilot e redundância de espelhos
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-09
RUN: GitLab pipeline 2930598862
COMMIT: GitLab b29fcbf0b3a7cc63e555f9564ec449b3c4b4b254 / GitHub 6f377a14e55b113f438398ace9593c9360bc9669
SUPERSEDES: test-hub/findings/20261009-1301-lease-wordpress-qa-redundancy-renewal.md

## PROVEN
- MR !18 merged no GitLab.
- GitLab main pipeline 2930598862 terminou SUCCESS.
- Pool de autocorreção inclui Gemini, Groq, Cloudflare, OpenRouter, Mistral, NVIDIA, Hugging Face e Vercel, com quota/cooldown e schema estrito do patch.
- Vercel passou a ser registrado no pool real do Anthares AI Hub.
- Fallback do GitHub Copilot Coding Agent foi instalado para incidentes de falha de código/runtime; falhas pré-runner são classificadas como infraestrutura e não geram patch especulativo.
- Reconciliador de espelhos fail-closed foi validado end-to-end: históricos divergentes com árvore idêntica convergem por merge de dois pais sem force; conteúdo divergente é recusado.
- GitHub main foi atualizado sem force para 6f377a14e55b113f438398ace9593c9360bc9669. A árvore b59c31bd09801554fbe8e5872dde21a2b49edddf corresponde ao conteúdo consolidado do GitLab main.
- Run GitHub 37891612002 foi repetido e voltou a falhar antes de qualquer step, com runner_id=0 e steps=[], confirmando falha de infraestrutura/alocação do GitHub-hosted runner, não falha do WordPress.
- GitLab CI executa QA de código independentemente do GitHub Actions e passou.

## Bloqueios externos restantes
- GitHub Actions continua falhando antes da alocação de runner; workflows novos também dependem da restauração desse serviço para execução no GitHub.
- Probe do GitLab confirmou GITHUB_MIRROR_URL ausente e credenciais ANTHARES_QA_SSH_* ausentes no GitLab; o reverse mirror e o QA híbrido de produção pelo GitLab estão definidos e fail-closed, mas não ativos.
- A atribuição do Copilot Coding Agent está implementada, porém não pode ser considerada E2E PROVEN enquanto o workflow GitHub não recebe runner e/ou a credencial/entitlement do agente não puder ser exercitada.

LEASE CLOSED
