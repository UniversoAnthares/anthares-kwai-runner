# Studio G4 — QA isolada da autorização de piloto e segurança Quill

STATUS: PARTIAL
DATE: 2026-11-17
AREA: anthares-studio/code-only/pilot-access-quill-fallback
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-pilot-fallback-safety-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/321
COMMIT: 2693c15293a9483a92ff928ae11af6b0088ebd82
SUPERSEDES: test-hub/findings/20261117-studio-pilot-fallback-lease.md

## Objetivo e alteração causal
- Corrigir o descompasso entre anst_can_use() e o gate administrativo do piloto sem conceder manage_options ao papel contador.
- Permitir somente IDs da opção anst_pilot_writer_ids explicitamente configurada; opção ausente/vazia bloqueia por padrão.
- Impedir que o fallback de Quill regrave Deltas com atributos ou embeds como texto simples.
- Preservar o plugin /estudio e os 71 registros originais e migrados.

## Evidência decisiva
- GitHub HEAD exata da branch PR #321: 2693c15293a9483a92ff928ae11af6b0088ebd82.
- Hostinger checkout efêmero por SSH Git autenticado já configurado: job Anthares Remote 273954e1c7e41a57e00bc7d31eba4abb, exit_code=0.
- Python unittest: Ran 72 tests; OK (72/72 PASS), inclusive stub PHP do gate individual.
- PHP 8.3: No syntax errors detected in anthares-studio/anthares-estudio.php.
- QA_MANIFEST_PREFLIGHT=PASS auditable=665 assigned=665 exactly_once=yes.
- Orquestrador QA: onze PASS e QA_COMPLETE.
- Primeira tentativa: 71/72 testes, falha por seletor estático adicional; corrigida causalmente na mesma branch antes de repetir.
- Checkout temporário eliminado pelo trap do script; nenhum arquivo escrito no computador pessoal.

## Consequência e fronteira da prova
- PROVEN em camada isolada: código e testes estáticos, mock de PHP; ainda sem validação de comportamento autenticado.
- A PR #321 fica DRAFT e depende de integração ordenada da PR #320 e do aceite G4.
- Não ativar a allowlist, ACF, publicação ou leitura externa sem teste funcional autenticado, permissões verificadas e rollback.
- Os bloqueios explícitos anteriores para navegador autenticado e CRUD REST não foram contornados.
- Nenhum merge, deploy ou mutação WordPress foi executado.
- Lease code-only finalizado com este finding; futuras mudanças requerem novo lease.
