# Neon produção: RLS habilitado, quatro papéis isolados; troca de credenciais bloqueada
STATUS: PARTIAL
AREA: kwai
DATE: 2026-11-13
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43535680082
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43535680082/job/132263983668
COMMIT: 79cc6b334c4405b6c7d5b18e2e34e0fbf09537d4
SUPERSEDES: 20261113-cortes-neon-rls-scoped-connections-running.md

## Resultado comprovado
No projeto Neon purple-flower-35918989, produção br-crimson-unit-b89nau08, public.cortes_publications passou de relrowsecurity=false/policies=0 a **relrowsecurity=true, relforcerowsecurity=false, policies=4**. A transação de DDL teve 15 statements confirmados. Quatro papéis PostgreSQL foram criados via SQL com LOGIN, NOBYPASSRLS e sem privilégio administrativo: cortes_kwai_primary_runtime, cortes_kwai_secondary_runtime, cortes_other_runtime, cortes_audit_runtime. Nenhuma senha foi definida para esses novos papéis. As políticas usam USING e WITH CHECK por target_key e uma política exclusiva de auditoria SELECT true. DELETE em cortes_publications foi negado aos quatro papéis.

Testes de produção SET LOCAL ROLE, SELECT real, em transações sem DML:
- primária: visible=640, kwai_primary=640, secondary=0, other=0, can_delete=false.
- secundária: visible=106, primary=0, secondary=106, other=0, can_delete=false.
- outras redes: visible=2345, primary=0, secondary=0, other=2345, can_delete=false.
- auditoria SELECT: visible=3092, sem DELETE.
Privilegios de tabelas auxiliares e sequências relevantes ao código do publicador generalista também concedidos explicitamente a cortes_other_runtime. A função de produção cortesqueue continua deploy 77 e recebeu health GET HTTP 200, database_ok=true, 16 itens de contagem. Seu indicador rls_attested=false permanece correto.

## CI e código preparado
Branch security/cortes-neon-rls-scoped-connections-20261113: SQL URL selecionada por AsyncLocalStorage em cada request (auditoria GET, principal/secondária em kwaiAction, outras redes em POST), falha segura se env da role ausente, no source fallback administrativo. Testes 43535680082: Node 41 PASS 0 FAIL, ALL_CANONICAL_WINDOWS_KWAI_REGRESSIONS_PASS. Quatro novas regressões NEON_KWAI_ACCOUNT_RLS_SCOPE_GUARD_PASS, NEON_HEALTH_RESTRICTED_AUDIT_ROLE_PASS, NEON_RLS_ROLE_MISSING_FAIL_CLOSED_PASS, NEON_KWAI_UNAUTH_NO_SQL_CALL_PASS.

## Bloqueio e limite
A tentativa de transferir as quatro URLs SQL secretas obtidas por integração Neon para o novo deploy na ramificação QA foi **explicitamente bloqueada pelas configurações de segurança da OpenAI**. A recusa foi respeitada; NÃO repetir por outra ferramenta, canal, controlador remoto, workflow ou reencaminhamento disfarçado. Deploy QA confirmado ainda 77; produção continua deploy 77 com DATABASE_URL padrão (neondb_owner, BYPASSRLS). Ainda NÃO ocorreu a migração das credenciais ou implantação do código novo, portanto NÃO declarar isolamento SQL end-to-end ativo em runtime. Flag pública network_isolation=false / rls_attested=false mantida. A atividade real Kwai permaneceu em produção com as filas intocadas; durante investigação principal 612 confirmed, 10 queued, 1 started e 1 uncertain; secundária 48 confirmed, 52 queued.

## Porta de promoção
Somente um procedimento autorizado de gestão de segredos (aprovado e executado diretamente pelo proprietário) poderá configurar senhas/URLs nos papéis e as quatro variáveis da função. Após isso, homologar bundle em QA com health, autorização, query/fencing/dedupe, e comprovar conexões postgres reais sem privilégios BYPASSRLS. Antes do deploy PROD: verificar versão 77, SHA de bundle, variáveis antigas preservadas, sem jobs em commit crítico. Depois: GET health 200, contagem Neon, proof de um job legítimo de cada conta e regressões de Instagram/Threads, preservando regras 06h–23h e zero duplicados.
Custo adicional: zero; nenhum segredo registrado no GitHub ou PC, nenhuma assinatura de RSA de dispositivo replicada.
