# Claude Code gratuito Anthares — aceitação real em nuvem
STATUS: PROVEN_CORE / PARTIAL_AUTO_PR
AREA: ai-remote-claude-router
DATE: 2026-10-19
LEASE: test-hub/findings/20261019-2209-lease-free-claude-remote-router.md
BASE_MAIN: b31164a7c771b06da3b98e147bdd698e5ededabd

## Evidências observáveis
- PLAN — PROVEN: run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39336129062, success. Bitwarden real, três modelos Gemini 3.x verificados, 9Router 127.0.0.1 com geração efetiva, resposta do Claude Code contendo ANTHARES_REAL_CLAUDE_PLAN_OK, cleanup success. PR #205 incorporado.
- Fallback técnico — PROVEN: run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39337326780, logs ANTHARES_FREE_9ROUTER_REAL_INFERENCE=PASS duas vezes e ANTHARES_FREE_FAILOVER_REAL=PASS. Modelo inicial artificialmente indisponível, saída real pelo modelo disponível seguinte.
- Edição real — PROVEN: mesmo run, ANTHARES_CLAUDE_EDITS_VALIDATED=PASS, ANTHARES_FREE_CLAUDE_RUN=PASS, ANTHARES_FREE_CLAUDE_REAL_EDIT=PASS. Única mudança: docs/anthares-free-claude-edit-canary.md, 2 linhas, EDICAO_REMOTA_CLAUDE_OK, blob 1ba4e1bb8994b204fe1b215d7991ee7cd6a0a582. Branch claude-free/proof-39337326780. PR draft #209: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/209. Não integrar arquivo de teste à main sem revisão.
- Sem VPS/PC de produção: GitHub Actions ubuntu-24.04 instala 9router@0.5.104 e Claude Code@2.1.290 temporariamente; Bitwarden SDK lê credencial Gemini existente. 9Router loopback, sem túnel; runners descartados após job. Não foi ativado billing ou contratado provedor pago.
- Regime degradado — PROVEN: no run #39337326780 o modelo Gemini 3.8 Flash deu NETWORK_ERROR, Gemini 3 Flash Preview 429, Gemini 3.5 Flash-Lite passou; sistema continuou com um modelo e registrou ANTHARES_FREE_ROUTER_DEGRADED_TO_ONE_MODEL=YES. Os demais modelos são testados novamente a cada novo bootstrap.
- Auto PR por GitHub Actions — PENDING_ADMIN_SETTING: a branch e o commit foram enviados pelo workflow, mas a criação de PR com GITHUB_TOKEN recebeu: "GitHub Actions is not permitted to create or approve pull requests". A integração GitHub instalada abriu PR #209 como substituto autorizado. Configuração externa necessária: repository Settings > Actions > General > Workflow permissions > Allow GitHub Actions to create and approve pull requests. Uma política mais restritiva da organização pode sobrepor a configuração do repositório.
- Escopo do modelo: plan sem ferramentas no canary, Read/Glob/Grep em planejamento real; Read/Edit/Write/Glob/Grep em edição; no Bash/MCP; checagem posterior de path exato; sem auto-merge.

## Limites da prova e pendências
- Não confundir fallback sintético de um modelo indisponível para um modelo funcional com capacidade contínua de dois ou mais modelos: no run de edição apenas um modelo real respondeu. Quotas e 429 são externos.
- Não é execução 24/7 de VPS: cada invocação dispara executor cloud efêmero. Repositório público mantém uso do GitHub Actions sujeito às políticas e limites do GitHub.
- A criação automática de PR depende do ajuste administrativo descrito acima. Nenhuma credencial deve ser colocada em logs, issues ou findings.
- O workflow de usuário está disponível em .github/workflows/anthares-free-claude.yml (workflow_dispatch); o ensaio separado foi .github/workflows/anthares-free-claude-edit-acceptance.yml.

SUPERSEDES: test-hub/findings/20261019-2209-lease-free-claude-remote-router.md
CONCLUSION: PLANNING_PROVEN; REAL_EDIT_PROVEN; FALLBACK_SWITCH_PROVEN; AUTO_PR_ADMIN_PENDING
