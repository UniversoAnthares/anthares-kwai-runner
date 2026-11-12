# CORTES R07.6 item 13 / ISO-07 — lease de verificação de admissão isolada
STATUS: RUNNING
AREA: architecture / tiktok / CORTES-ISO-07
DATE: 2026-10-25
OWNER: chatgpt-ops-iso07
JOB: ISO07-20261025-EXEC
BRANCH: chatgpt/r07-iso07-readiness-qa-20261025
BASE: 183f6a8eda4d2585f6cdd73982984a66df541802
SUPERSEDES: none

## BASELINE_PROVEN
Preflight local f6fc9ca59a96e451 PASS; audit 218/0. Documentação GitHub/main permanece 2e28d54043d6bad1, divergência coberta na PR governance#7. GitHub main tem workflows cloud/Windows da conta TikTok lucasrosalem4 sem Environment dedicado, conforme SHA 19d6cb6c2172025be30b502184b02670a34510a6 e 9ba07142ef7676dfcdff027e600e074482a0d896. Neon produção: public.cortes_publications e public.cortes_tiktok_lucasrosalem4_publications com RLS=false, FORCE=false e zero policies, SELECT read-only de 25/10/2026; neondb_owner possui BYPASSRLS. PRs #1332, #1338 e #1381 contêm contratos/QA sem IAM integral de produção.

## FAILED_AVOIDED
Env dedicado e downgrade de role Neon foram anteriormente negados por segurança/permissões; não reproduzir operações negadas usando outro conector. Nenhum deploy, secret, DDL, publicação, replay UNCERTAIN, manipulação de fila ou token neste ensaio. Não mexer nos arquivos das PRs #1332/#1338/#1381 nem nas sessões e processos existentes.

## SUCCESS_SIGNAL
Criar diagnóstico fail-closed sem permissões de publicação que verifica workflows reais e metadados documentais, enumera lacunas de admissão de uma conta e bloqueia falso READY mesmo com evidência autodeclarada. Testar com casos positivos/negativos em fixtures isoladas e, se viável, CI read-only sem secrets.

## FAILURE_SIGNAL
Admissão positiva por falta de dados, alegação de acesso cruzado por testes estáticos, publicação/integração produtiva, alteração de outro escopo, vazamento de secret, dependência de privilégio superusuário ou falha na limpeza das fixtures.

## TEST_VALIDITY
Testes executam em diretórios descartáveis/QA. Um PASS de testes de código não equivale a IAM, RLS, writer e canário em produção. O estado fixo do item 13 permanece PENDENTE até recibo externo de uma conta realmente segregada.

## LEASE
Somente novos caminhos qa/iso07/* e este finding, pertencentes a esta branch exclusiva. Sem interferência nos testes, branches ou publicadores de outros agentes. Encerrar com finding append-only e registro no checklist oficial.
