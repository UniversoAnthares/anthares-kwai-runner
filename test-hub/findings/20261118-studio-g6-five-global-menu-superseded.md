# Correção G6 — atividade paralela já implantou a mesma alteração
STATUS: SUPERSEDED
AREA: anthares-studio/navigation
DATE: 2026-11-18
JOB: studio-g6-five-global-menu-20261118
SUPERSEDES: 20261118-studio-g6-five-global-menu-lease.md
SOURCE: UniversoAnthares/anthares-wordpress PR #325 e PR #326.
EVIDENCE: Hostinger JS atual SHA256 4b330c81097819f6d4ef71cd0e651c1af6306fa4cc152fd4ccd5b7258c6df29e, após remoção de Lixeira do menu global; o atalho contextual permanece em Meus projetos. PR #325 registra publicação anterior. PR #326 reúne regressões de navegação, ações, CSS e lixeira em 91/91 testes.
QA_EXTRA: Browserless sintético antes/depois do patch isolado da PR #327, 1366x768 e 390x844, 28 etapas sequenciais, cinco destinos globais, sete grupos internos, Lixeira contextual e zero exceções. Este ensaio testa frontend isolado e não substitui cliques reais na conta autenticada.
DECISION: encerrar a PR #327 sem merge para evitar duplicação. Encerrar lease PR #2652; a implementação já existente mantém prioridade. Preservar todos os dados e o plugin /estudio; nenhuma mudança em produção foi feita por este job.
