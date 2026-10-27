# CI quota controller — Neon/Vercel production and real GitLab-to-GitHub handoff
STATUS: PARTIAL
AREA: architecture / ci-quota-live
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40510130758
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40510130758/job/122209533226
COMMIT: f2aa0799ac547ece21a974d7e6a860d58800cf55
SUPERSEDES: test-hub/findings/20261027-ci-quota-postgres-real-qa-rollback-proven-chatgpt.md

## Instalações efetivas

1. Neon main project purple-flower-35918989 / branch br-crimson-unit-b89nau08: tabela public.anthares_ci_quota_attempts + índice de lease criados transacionalmente; zero linhas no momento da implantação. Revogado acesso de PUBLIC.
2. Um papel criado pela API Neon herdava neon_superuser: foi imediatamente substituído por anthares_ci_quota_limited, criado por SQL com NOINHERIT NOCREATEDB NOCREATEROLE NOBYPASSRLS. SELECT/INSERT e UPDATE colunas específicas concedidos apenas na tabela CI; sem INSERT em cortes_publications. Papel temporário excessivo excluído. Senhas não versionadas.
3. Vercel projeto separado anthares-ci-quota-controller, DATABASE_URL como variável sensitive, papel limitado. Endpoint /api/health retornou HTTP 200, ledger=READY e mode=ENABLED.
4. Rotas implantadas: /api/cancel (OIDC GitHub vinculado ao run próprio), /api/gitlab-reserve (OIDC do watcher + GitLab pipeline terminal com ci_quota_exceeded e ausência de jobs ativos estranhos), /api/gitlab-ack (registro de HTTP 204 do dispatch), /api/gitlab-confirm (conciliação com run GitHub completed/success). Falhas deixam estado incerto sem reenvio.
5. PR #1531 incorporou reserva antes do dispatch no watcher GitLab; PR #1532 retirou preflight offline que impedia job real; PR #1534 adicionou ACK do dispatch; PR #1537 instalou leitura independente da conclusão.

## Evidência observada em execução produtiva

- GitHub watcher run 40510130758/job 122209533226: conclusão SUCCESS, credencial GitLab obtida de Bitwarden, registro DISPATCHED cortes pipeline=2994547840. Nenhum post social foi acionado pelo watcher.
- Neon registrou gitlab:87307248:2994547840, FALLBACK_RESERVED, SHA bb64681264e6ca6c1665b0d398dcfd7c101225e3 antes do dispatch.
- GitHub workflow de redundância run 40510154187 com display_title quota-rescue-cortes-glsha-bb64681264e6ca6c1665b0d398dcfd7c101225e3 terminou SUCCESS.
- Fechamento manual condicionado a esse SHA e run id atualizou registro Neon para FALLBACK_CONFIRMED e incrementou geração de 1 para 2.
- Watcher run 40510955234, depois da PR #1534, concluiu SUCCESS e não repetiu um evento previamente atendido. Run 40511555273, após PR #1537, também concluiu SUCCESS, registro DEDUPED sem despacho duplicado.

## Pendências honestas

- A observação de um GitLab quota pipeline ativo exclusivamente próprio recebendo CANCEL remoto ainda não ocorreu: os casos reais vistos já estavam FAILED pelo provedor.
- A transição automática /api/gitlab-ack e /api/gitlab-confirm está instalada em produção, mas não foi observada num novo evento elegível após o deployment.
- /api/cancel para GitHub run próprio está publicado, porém nenhum workflow existente invoca tools/ci_quota_signal_github.py por um erro genuíno e estruturado de quota. Não declarar universalidade.
- CORTES Clipper PR #213 permanece draft sob atuação paralela; o consumidor real de outbox por conta/plataforma e demais adaptadores faltam.
- WordPress QA P0 está funcional por leitura SSH somente no runner autorizado (run 40502501489), mas WP Application Password e REST Basic autenticado continuam sem provisionamento direto.

## Regra para próximos agentes

Preservar a prova real, credenciais restritas, identidade OIDC e os gates de lease. Não disparar testes sintéticos nem publicações para fabricar um incidente. Não transformar FALLBACK_SUBMITTED em FALLBACK_CONFIRMED sem GET independente do run exato e conclusão success. Não reiniciar a pipeline GitLab original e não desligar jobs de terceiros. Não alegar cancelamento real se o provedor já havia tornado a pipeline terminal.
