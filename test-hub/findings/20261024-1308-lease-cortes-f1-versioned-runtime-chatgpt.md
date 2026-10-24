# CORTES F1 — lease de versionamento isolado do runtime
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-24
LEASE_OWNER: chatgpt-cortes-drive-f1-runtime-20261024
EXPIRES_UTC: 2026-10-24T17:37:00Z
RUN: Anthares Remote job 8c1b55fcee27c0ef05ccce185f2c97db
JOB: versionar os scripts F1 sem mexer na fila/publicadores
COMMIT: anthares-clipper main efb4b1b9676f1316e2f9f159fd8988dffe679473; stage guard 8fa0934c60e2401d31cffcb6f0b9d89740dd7402
SUPERSEDES: none
BASELINE_PROVEN: finding 20261024-1306-cortes-drive-f1-scheduled-synthetic-recovery-partial.md, merged 5dd788b; task SYSTEM/30min ativa; 2x readback e recuperação lock.
FAILED_AVOIDED: não mesclar PR amplo #190, não reusar OAuth partilhado, não sobrescrever branches/arquivos concorrentes, não alterar rede social.
SUCCESS_SIGNAL: PR isolado com scripts sem credenciais, código do runtime instalado reconstruível, checks e revisão sem deploy cego.
FAILURE_SIGNAL: mudanças concorrentes de HEAD, GitLab diverge, conflito no main, teste reprovado, segredo detectado.
TEST_VALIDITY: versão em Git é distinta da versão efetivamente implantada; PR não é deploy. Runtime atual fica preservado.
SCOPE: código + documentação para reinstalar replicador Google Drive F1, nenhum agendamento novo.
