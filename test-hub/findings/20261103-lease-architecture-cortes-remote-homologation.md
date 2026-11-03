# Lease — homologação somente leitura da continuidade remota de CORTES
STATUS: RUNNING
AREA: architecture
DATE: 2026-11-03
RUN: none
JOB: read-only-provider-diagnostics
COMMIT: e5d105d24565b013ca1624cbcd5631dbb9dae403
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / CORTES
LEASE_START_UTC: 2026-11-03T21:03:18.051Z
LEASE_EXPIRES_UTC: 2026-11-03T21:28:18.051Z
GOVERNANCE_MANIFEST: 223433740e807a90

## BASELINE_PROVEN
- Cutover do Clipper para execução remota permanece PARTIAL. Os cron Windows foram removidos de main no commit 8c31afffe137a9ed1d9860d10e8c8d380b3a86ec.
- Preflight GitHub-hosted somente-leitura PROVEN no run 41116819377.
- Banco Neon existente, sem novas tabelas ou projetos; ações externas limitadas a probes de saúde sem dados e SQL SELECT.
- Dados de usuários/mídia permanecem privados; o computador pessoal não é usado como runner, armazenamento ou staging.

## FAILED_AVOIDED
- Não publicar vídeo, não atualizar fila/ledgers, não retomar UNCERTAIN, não habilitar GitHub Actions adicionais ou tarefas locais.
- Não executar rota Vercel após HTTP 402 nem contratar plano/crédito.
- Não fazer cutover antes de prova de mídia, autenticação, identidade, fencing e quota independente.

## SUCCESS_SIGNAL
- Finding append-only de homologação contendo provas de health externo, OIDC denial sem credenciais, integridade de snapshots e restauração da mídia, com classificação de bloqueios e escopo bem delimitado.
- Nenhuma alteração em produção, fila, mídia, projeto Neon, Worker, Vercel ou scheduler.

## FAILURE_SIGNAL
- Change concorrente na fonte, teste de produção involuntário, segredo exposto ou prova de integridade divergente.

## TEST_VALIDITY
Esta lease autoriza exclusivamente documentação de evidência observada, sem alterar códigos/serviços de CORTES. Encerra-se no finding terminal na mesma PR, quando merged. Nova lease exigida antes de qualquer implantação.
