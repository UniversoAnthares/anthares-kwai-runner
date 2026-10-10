# Lease — Copilot CI Expert replacement
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-10
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none
LEASE_EXPIRES: 2026-10-10T11:15:00-04:00

## Objetivo
Versionar um agente `ci-expert` do GitHub Copilot CLI como substituto permanente e gratuito do GitLab Duo CI Expert, preservando GitLab CI e GitHub Actions como provedores de execução e deixando mutações remotas sob controle do ChatGPT/conectores.

## BASELINE_PROVEN
- GitHub Copilot Free já autenticado no VS Code (`free_limited_copilot`).
- Copilot CLI v1.0.95 instalado e validado localmente.
- Agente local `ci-expert` respondeu `CI_EXPERT_READY`.
- Smoke read-only respondeu `PROVIDERS_OK github=yes gitlab=yes`.
- `AGENTS.md` e `test-hub/README.md` foram lidos nesta rodada.

## FAILED_AVOIDED
- GitLab Duo Agent Platform exige trial temporário ou créditos; não será usado.
- Não usar Copilot cloud agent pago como dependência.
- Não alterar CI de produção nem runners nesta prova.

## SUCCESS_SIGNAL
- `.github/agents/ci-expert.agent.md` existe na branch de implementação.
- Copilot CLI reconhece `--agent ci-expert` e executa um smoke read-only no repositório sem modificar arquivos.
- Nenhum push/merge/deploy é executado pelo agente.

## FAILURE_SIGNAL
- Perfil não é carregado pelo Copilot CLI, ou o smoke não consegue ler os provedores GitHub/GitLab presentes no repositório.

## TEST_VALIDITY
- O teste é inválido se o HEAD base mudar antes da criação da branch sem reconstrução da mudança, se houver lease ativo anterior para esta mesma área/objetivo, ou se o Copilot usar outro agente/perfil.

## Segurança
Nenhum secret, cookie ou token é gravado. Navegador normal do usuário não é usado. Esta mudança só adiciona configuração de agente e evidência do Test Hub.
