# CORTES R07.6 item 13 — diagnóstico de admissão fail-closed em Windows, 10/10 PASS
STATUS: PROVEN (somente verificador QA); ITEM 13: PENDENTE EM PRODUÇÃO
AREA: architecture / tiktok / CORTES-ISO-07
DATE: 2026-10-25
OWNER: chatgpt-ops-iso07
JOB: ISO07-20261025-EXEC
RUN: Anthares Remote Windows job d0b5c32422c65e6a9df322beb55a7281
COMMIT: a2a9a158a5788d2f1a7fc473ccb148fd8fea9ab5
SUPERSEDES: test-hub/findings/20261025-iso07-readiness-lease.md

## Implementação e fonte
Branch isolada chatgpt/r07-iso07-readiness-qa-20261025, novos arquivos qa/iso07/preflight.py (blob 50ffd4b31d0ef315355a70bba723a36343c81642), qa/iso07/test_preflight.py (blob bc63de049551deb07b952eb79a0ca8b3b60a9d6b), qa/iso07/README.md e __init__.py. Operação estritamente de leitura sem credenciais, sem chamadas ao publicador, sem schema/queues/CI produtivo. Referência da conta: TikTok lucasrosalem4, contrato de escopo na PR #1332 e publicadores GitHub/main.

## Prova real do Windows e do estado externo
Preflight documental PASS f6fc9ca59a96e451; audit 218/0. Github main consultado para dois workflows; Neon produção purple-flower-35918989 consultado em SELECT real, retornando:
- public.cortes_publications: RLS=false, FORCE=false, zero policies.
- public.cortes_tiktok_lucasrosalem4_publications: RLS=false, FORCE=false, zero policies.
- neondb_owner: LOGIN=true, BYPASSRLS=true, CREATEROLE=true.
O snapshot entregue ao verificador foi sanitizado, montado dos resultados de leitura autenticada nesta execução; nenhum segredo/token saiu.

### Teste de execução
Anthares Remote Windows job d0b5c32422c65e6a9df322beb55a7281.
- 10 testes unittest reais: Ran 10 tests in 0.001s; OK; UNITTEST_EXIT=0. Incluíram isolamento de conta, ambiente GitHub dedicado, uso indevido de secret de Kwai, RLS, role BYPASSRLS, negativas bidirecionais e proibição de publicação por mera declaração de provas.
- CLI aplicada aos workflows vivos de main e ao ownership na branch da PR #1332 com diagnóstico Neon: ADMISSION_EXIT=0; status=BLOCKED; blocked_gates=22, authorized_to_publish=false, live_publication_invoked=false.
- Processos Python encerrados ao fim de cada chamada; pasta temporária criada pela execução removida: ISO07_TEMP_REMOVED=True. Falhas temporárias de fixtures (escape Python e BOM UTF-8 do Windows) foram corrigidas no código antes da rodada aprovada; nenhum serviço de produção foi testado por publicação.

## Limite explícito
PROVEN refere-se exclusivamente à detecção fail-closed em execução real e à auditoria de metadados. Testes com dados declarados não autorizam publicação. ITEM 13 NÃO HOMOLOGADO: ainda faltam Environment GitHub e identidade própria sem acesso transversal; roles LOGIN com NOBYPASSRLS, RLS/FORCE e negativas bidirecionais reais; writer exclusivo integrado ao publisher; reconciliação; mídia editorial real, limite de quota e rollback isolado; canário público com ID/conta/arquivo confirmado. Provisão de Environment e alteração de roles foram previamente barradas por controles de segurança/autoridade: não repetir via outra integração.

## Recuperação e risco
Como só foram acrescentados arquivos QA a branch exclusiva, rollback limita-se à revisão/fechamento da branch/PR; production unchanged. Nenhuma tarefa/agendamento/segredo/processo/conta produtiva foi alterado. Não promover o item 13 ou qualquer controle dependente com base neste resultado.
