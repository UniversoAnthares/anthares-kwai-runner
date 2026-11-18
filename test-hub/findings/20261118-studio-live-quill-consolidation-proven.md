# Studio — consolidação Quill e lixeira: QA de código aprovada

STATUS: PROVEN
DATE: 2026-11-18
AREA: anthares-studio/release/staging-live-quill-safety
OWNER: ChatGPT / OBSERVATORIO IPB
JOB: studio-live-quill-consolidation-20261118
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/334
COMMIT: eaafdd08454d6780474626dc2fba5a856489128f
SUPERSEDES: test-hub/findings/20261118-studio-live-quill-consolidation-running.md

## Implementação versionada
- PR #334 DRAFT derivada do código da PR #333 (Quill2, toolbar isolada, Ctrl+Z inicial protegido).
- Mantém ajuste da produção de que a limpeza automática da lixeira está desativada ou ativada segundo a flag anst_trash_cleanup_enabled; o inline PHP privado expõe trashCleanupEnabled.
- Testes e contratos atualizados para ações adicionais válidas do frontend, para history.clear após setContents e para conversão CSS exata #post-21383 -> #post-19344 sem modificar o CSS.
- Manifestos de QA raiz e empacotado incluem os três arquivos novos do Quill, exactly-once.

## QA diretamente observada
- Hostinger privada, clone efêmero da HEAD eaafdd08454d6780474626dc2fba5a856489128f.
- Python3 -B unittest discover: Ran 96 tests, OK (96/96 PASS), job 9285701baba23e7121f5a91656a5ee33.
- PHP 8.3 lint: todos os módulos e fixtures PHP de anthares-studio PASS; job 1e9cb7355b9f514e02a990313a122112.
- Bun 1 módulo compilado: 202.75 KB, PASS.
- QA_MANIFEST_PREFLIGHT=PASS auditable=679 assigned=679 exactly_once=yes.
- Orquestrador QA: 11/11 PASS.
- Manifesto e espelho SHA256 cb093e264cdfc482c87741e9afdfce66408737b6e0fbec06fe1bbbbb0c26ba11, idênticos.
- Todos os checkouts efêmeros removidos em EXIT. Nenhuma gravação em dados reais.
- Produção conferida em 2026-11-18 16:18 UTC: JS SHA256 1b2b499310e28db0abb9bd0c3085c2ac4f5a1c4d0fd381208378b8e8602224f1; PHP Studio 36b83bf049767d60b8fe4e9345e312f8423ab80818ef83e8ce98e408e7c9f9e0; PHP original 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.

## Limites e consequência
PROVEN se aplica exclusivamente ao QA de código integrada na branch da PR #334. O JS ativo ainda não contém toolbar isolada e history.clear. Lease Test Hub #2654 RUNNING para alterações de JS em produção, portanto sem escrita nem deploy para evitar conflito. Teste real de CRUD autenticado e acesso à aba privada tiveram bloqueios explícitos anteriores das ferramentas e não podem ser reproduzidos por outro canal. G4 funcional, G5 end-to-end, G6 visual, G7 188 requisitos e G8 aceite final permanecem pendentes. Antes de promoção: reconciliar lease, backup privado, hash atual, retorno seguro, testar desktop/mobile com autorização e revisar outros agentes em execução.
