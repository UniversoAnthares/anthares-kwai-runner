# AOI #14 — revisão terminal de publicação TikTok real histórica
STATUS: RUNNING
DATE: 2026-11-04
ITEMS: [14]
AREA: tiktok-historical-real-post-acceptance
OWNER: chatgpt-reestruturacao-20261104
LEASE_OWNER: chatgpt-reestruturacao-20261104
LEASE_EXPIRES: 2026-11-04T19:11:05.851Z
BASE_HEAD: bde5364b90efc68925be560c429a8704257c691e
GOVERNANCE_MANIFEST: 223433740e807a90
TARGET_SOURCE_BLOB: c62544773c982a60b2b470f068a4c9dcb437ad8d
TARGET_JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40415232407
TARGET_JOB_ID: 121895778546
RUN: read-only-GitHub-Actions-and-Neon
JOB: none
SUPERSEDES: none

BASELINE_PROVEN: histórico real de publicação em 2026-10-26 @lucasrosalem4 com preflight conta, fence, confirmação pós-upload no Studio e receipt Neon com exact remote_id; source blob idêntico no GitHub main, commit do run e GitLab peer. Critério terminal item14 = prova histórica de publicação real com identidade correta, sem inferir migração Forgejo.
FAILED_AVOIDED: nenhum novo upload, publicação, job, reenvio de 10 TikTok uncertain ou 68 Kwai uncertain; nenhuma mudança no item15 ou nas flags/segredos das contas.
SUCCESS_SIGNAL: readback de GH Actions run+job e conteúdo de logs, SHA histórico de fonte, id/UTC no Neon, gate de identidade+fence+perfil pós-publicação e PR documental com finding terminal. Marcar DONE apenas item14.
FAILURE_SIGNAL: remote_id divergente, conta incorreta, log de fixture em vez de publisher, ausência de confirmação no Neon, ou publicação sem fence; preservar PARTIAL se qualquer gate falhar.
TEST_VALIDITY: observação de fato histórico em produção por provedor GitHub Actions e banco Neon, sem disparar mídia; TikTok público bloqueia leitura anônima, não é alegada acessibilidade pública atual.
ROLLBACK: revert documental/estado técnico mediante nova evidência; nenhum efeito em banco.
