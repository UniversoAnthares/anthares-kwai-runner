# cortesqueue Neon — migração para quatro conexões RLS
STATUS: RUNNING
AREA: kwai
DATE: 2026-11-13
RUN: none
JOB: none
COMMIT: e3a0e10bfa7f48c798abe8e3bc58ea78ec6367eb
SUPERSEDES: 20261113-kwai-rls-qa-fresh-isolation-proven.md

## BASELINE_PROVEN
Production cortesqueue deploy 77 usa process.env.DATABASE_URL, role neondb_owner BYPASSRLS. public.cortes_publications em produção relrowsecurity=false, zero policy. QA branch br-plain-surf-b8vupkq8 teve RLS testado por SET ROLE e os novos papéis de LOGIN realmente separados: cortes_kwai_primary_runtime_qa acessa 640 linhas da primária e zero linhas de outras contas; cortes_kwai_secondary_runtime_qa 106 somente secundária; cortes_other_runtime_qa 2345 somente não Kwai; cortes_audit_runtime_qa todas 3092 só leitura; todos NOBYPASSRLS e sem DELETE na tabela. Todas as filas de produção permanecem intactas.

## FAILED_AVOIDED
Não ativar FORCE RLS na produção com outras funções Neon/consumidores ainda sob neondb_owner. Não instalar segredos no PC ou GitHub. Nunca reproduzir assinatura RSA do dispositivo manualmente após a recusa de segurança documentada. Não intervir em leases Android nem testar post com mídia. Não presumir que UPDATE em QA ou build verde sozinho prove runtime.

## SUCCESS_SIGNAL
Cortesqueue usa papel Kwai por conta e papel não-Kwai para mutações gerais; GETs de saúde usam papel SELECT. Query fail closed quando o roteador SQL/variável requerida falta; os quatro papéis foram testados com login real em QA. CI passa testes de sintaxe, roteamento, pacing e regressões. Deploy QA health e mensagens de rejeição conservados. Implantação PROD só após prova de ambiente completo, SQL RLS e credenciais com validação; confirmação via processos legítimos e monitor de fila, sem repetir gravações.

## FAILURE_SIGNAL
Conexão de dono/BYPASSRLS em caminho protegido, CROSS_ACCOUNT_ROWS>0, perda de variáveis existentes, 5xx no health, quebra dos outros canais, CI vermelho ou incerteza sobre source bundle.

TEST_VALIDITY: testes sintéticos sem postagem; PostgreSQL QA isolado; migração sem novos custos, sem perda de disponibilidade.
