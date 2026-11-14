# Neon CORTES: RLS de produção e promoção do runtime

**Estado (13/11/2026):** RLS da tabela public.cortes_publications habilitado em produção, com quatro políticas e quatro papéis de privilégio limitado. Runtime Neon Function cortesqueue ainda na versão 77 e ainda usando neondb_owner/BYPASSRLS. Migração de credenciais e deploy do código deste branch pendentes por bloqueio explícito da transferência de segredos.

## Instalação SQL já realizada
Projeto purple-flower-35918989, branch br-crimson-unit-b89nau08:
- cortes_kwai_primary_runtime: LOGIN NOBYPASSRLS, SELECT/INSERT/UPDATE sobre cortes_publications, policy target_key='kwai:lucasrosalem'.
- cortes_kwai_secondary_runtime: mesmo escopo para target_key='kwai:universoanthares'.
- cortes_other_runtime: SELECT/INSERT/UPDATE sobre cortes_publications, policy target_key NOT LIKE 'kwai:%'. Acesso às tabelas auxiliares de buffer, orçamento, scans autenticados e HA, DELETE apenas nas tabelas auxiliares específicas e USAGE em sequências.
- cortes_audit_runtime: SELECT em cortes_publications, policy somente leitura, todas as linhas.

Nenhum papel possui BYPASSRLS, neon_superuser, CREATEROLE ou DELETE em cortes_publications. Os logins foram criados por SQL sem senha.

## Código preparado isoladamente nesta branch
A função usará exclusivamente quatro variáveis com URLs SQL distintas:
- CORTES_KWAI_PRIMARY_DATABASE_URL
- CORTES_KWAI_SECONDARY_DATABASE_URL
- CORTES_OTHER_DATABASE_URL
- CORTES_AUDIT_DATABASE_URL

O código escolhe escopo a partir do target_key Kwai validado, e health GET recebe papel audit. Não existe fallback administrativo; variável ausente causa falha segura.

## Porta de promoção
1. O proprietário, por fluxo autorizado de gestão de credenciais Neon, define senhas fortes e privadas para os quatro papéis sem ampliar privilégios e confere rolbypassrls=false.
2. Configura as quatro URLs como variáveis secretas da Neon Function cortesqueue nas ramificações de QA e produção, preservando segredos anteriores. Não registrar senhas em repositório, PC, tickets, mensagens ou logs.
3. Publica bundle com index.mjs, kwai-pacing-policy.mjs, kwai-persistent-cloud-identity.mjs e kwai-oneoff-public-reconcile.mjs em QA somente após verificação de integridade e variáveis.
4. Valida health GET, isolamento por conta SQL, autorização de ações Kwai e prova por executor legítimo, além de Instagram/Threads. Não simular assinatura RSA manualmente após bloqueio de segurança.
5. Coordena produção sem operações irreversíveis em progresso, mantém rollback do bundle, valida HTTP 200, SQL current_user em cada papel, reconciliação, status reais e zero duplicatas.
6. Só após prova completa, reavaliar rls_attested:false. network_isolation é declaração distinta que exige prova independente.

**Bloqueio vigente:** a transferência de URLs SQL secretas entre as ferramentas para deployment foi recusada pelos controles de segurança da OpenAI. Respeitar e não repetir por outros canais/controladores sem autorização do processo. Código permanece em PR draft para evitar implantação sem credenciais.

Test Hub: test-hub/findings/20261113-cortes-neon-prod-rls-activated-runtime-credentials-blocked.md. CI #43535680082: 41 PASS, 0 FAIL, regressões Python aprovadas. SQL de produção comprovado: 640 linhas primária, 106 secundária, 2345 outras e 3092 audit.
