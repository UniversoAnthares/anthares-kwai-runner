# Lease — implementação real multi-provedor cancel-first
STATUS: RUNNING
AREA: github-ci/quota-provider-cancel
DATE: 2026-10-27
RUN: none
JOB: none
COMMIT: 56afcc6034b199e387149938f8297c9b1a46dd21
SUPERSEDES: none

Owner: ChatGPT. Escopo único: implementar adapters AppVeyor e Bitrise com status e cancelamento próprio, integrar com controlador Vercel exclusivo (GitHub OIDC watcher), adicionar caminho operacional de execução apenas para eventos confirmados, sem disparo sintético e sem mexer em publicadores. Lease 30 min, branch isolada.
BASELINE_PROVEN: GitLab terminal -> reserva Neon -> GitHub redundância real, https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40510130758, PRs #1531,#1534,#1537.
FAILED_AVOIDED: nenhuma cancelamento de jobs alheios, nenhuma inferência de quota a partir de HTTP500, nenhum redespacho com status incerto, não reusar tokens de outro serviço.
SUCCESS_SIGNAL: adapters de dois novos provedores conectados à mesma tabela principal e host cloud com identidade controlada; implantação efetiva confirmada.
FAILURE_SIGNAL: API sem identidade inequívoca, token ausente, job em estado incerto: registrar CANCEL_UNCONFIRMED, jamais reexecutar.
TEST_VALIDITY: não fabricar ocorrência; verificar deployment e integrações sem intervir em publicação.
