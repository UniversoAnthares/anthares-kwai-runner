# Copilot CI Expert replacement — permanent free path proven
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-10
RUN: none
JOB: AI Commander 9bd6664b56864748
COMMIT: f8aa65cd5036a64a94fd9dc42513f5206af32df8
SUPERSEDES: test-hub/findings/20261010-1043-lease-architecture-copilot-ci-expert.md

## Objetivo
Fechar a substituição do GitLab Duo CI Expert por um agente permanente baseado no GitHub Copilot Free/CLI, mantendo GitHub Actions e GitLab CI como provedores e sem depender de trial de 30 dias, compra de créditos ou cartão.

## Resultado
- GitHub Copilot Free já estava autenticado no VS Code; o log registra SKU `free_limited_copilot` e token presente, sem expor o token.
- GitHub Copilot CLI v1.0.95 foi instalado via WinGet.
- Smoke básico não interativo retornou `COPILOT_CLI_READY`.
- Wrapper seguro `C:\Users\Lucas\AntharesWork\anthares-copilot-agent.ps1` foi criado e retornou `WRAPPER_READY`.
- Agente especializado `ci-expert` foi criado e o teste local retornou `CI_EXPERT_READY`.
- O agente leu o repositório em modo somente leitura e retornou `PROVIDERS_OK github=yes gitlab=yes`.
- A definição versionada `.github/agents/ci-expert.agent.md` foi validada diretamente a partir desta branch, após renomear o fallback de usuário para impedir precedência acidental; o job AI Commander `9bd6664b56864748` retornou `REPO_CI_EXPERT_READY`.
- O workspace `C:\Users\Lucas\anthares-duo-test` mantém remotes separados `github` e `gitlab`; nenhum force-push ou blind mirror foi usado.

## Evidência decisiva
- `COPILOT_CLI_READY`
- `WRAPPER_READY`
- `CI_EXPERT_READY`
- `PROVIDERS_OK github=yes gitlab=yes`
- `REPO_CI_EXPERT_READY`
- Branch de implementação: `agent/copilot-ci-expert-replacement`
- Commit de implementação: `f8aa65cd5036a64a94fd9dc42513f5206af32df8`

## Segurança
- Nenhum navegador visível foi usado.
- Nenhum secret, cookie ou token foi gravado no repositório ou nos findings.
- O agente não recebeu autorização para push, merge, deploy, publicação ou alteração de secrets/produção; essas mutações permanecem no controlador ChatGPT/conectores.
- O GitLab peer estava divergente/stale em relação ao GitHub atual e, por isso, não foi force-mirrored.

## Consequência
- PROVEN: GitLab Duo Agent Platform não é necessário para o CI Expert do Anthares.
- Usar `ci-expert` via Copilot CLI/VS Code como camada auxiliar gratuita, e GitHub/GitLab connectors como camada de mutação controlada.
- Não iniciar trial do GitLab Duo apenas para esta finalidade.
- Preservar o wrapper e as regras fail-closed; não liberar push/merge/deploy direto ao agente sem nova revisão específica.
