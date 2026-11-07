# 07/08 — recuperação stateful exige aprovação explícita
STATUS: PARTIAL — CODE_READY
AREA: operations/ara-backup-release-and-emergency
DATE: 2026-11-06
LEASE: lease-opt07-08-ara-stateful-approval-20261106.md — CLOSED
SUPERSEDES: 20261106-opt07-08-ara-release-protection-ready.md
BASELINE_PROVEN: PR #2137 incorporou deploy stateless com SHA aprovado e lock compartilhado; rota stateful possuía dois modos de disparo manual sem SHA.
IMPLEMENTED: workflows cloudflare-ara-backup-deploy.yml e trigger-cloudflare-ara-backup-deploy.yml exigem release_sha de 40 caracteres, incidente e booleano acknowledge_override=true. O stateful permite somente SHA da historia main e impede execucao por ref fora da main; o dispatcher encaminha os tres inputs. Lock do Worker compartilhado sem cancelar outro deploy.
SUCCESS_SIGNAL: merge sem disparo de release; qualquer futura recuperação exige ato expresso com incidente e SHA; sem modificacao no Worker atual.
FAILURE_SIGNAL: incidente ausente, SHA divergente, ref errada ou checkbox ausente => nenhuma implantacao.
TEST_VALIDITY: guardas de texto e correspondencia dos inputs; nenhum job de deploy foi executado.
COST_ADDED: R$0.
