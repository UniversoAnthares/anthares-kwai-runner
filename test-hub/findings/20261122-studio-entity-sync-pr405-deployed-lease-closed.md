# Anthares Studio — sincronização de entidades narrativas, item 18

DATA: 2026-11-22 (America/Campo_Grande).
OWNER: ChatGPT / STUDIO_ENTITY_SYNC_20261122.
LEASE: test-hub/findings/lease-studio-entity-sync-20261122.md (renovado em lease-studio-entity-sync-renew-20261122.md). STATUS=CLOSED_SUCCESS.
GITHUB: UniversoAnthares/anthares-wordpress PR #405 integrado, merge 27a608dc2fbb4015bd2b57fd44019303fbe2e75a.
STATUS: DEPLOYED_AND_TRANSACTIONAL_QA_PASS. AUTHENTICATED_VISUAL_QA_PENDING_IN_ITEM_21.

## Escopo executado
- Domínio de entidades narrativas: revisão SHA256 incluindo ACF, dados canônicos e cronologia; revisão obrigatória em POST/DELETE, lock SQL por ficha com cronologia compartilhando lock de cena; update sob transação; rejeição de versão obsoleta com erro HTTP409.
- Escrita de cenas/acontecimentos/beats propaga ordem de leitura, ordem cronológica e tempo para a mesma entidade da linha do tempo, mantendo ID e histórico, além de dados ACF em análises.
- Bloqueia exclusão quando relação ACF, referência `aestEntity` no Delta, marcador de personagem no Delta, aparição confirmada, âncora cronológica relativa ou ficha filha ainda depender do mesmo ID.
- JS em `estudio.js`, `studio-g7-workspaces.js`, `studio-narrative-timeline.js`, `studio-character-appearances.js`: invalidam caches e exibem dados canônicos das fichas, personagens, relações e análises após atualização. BroadcastChannel avisa outras abas da mesma origem; formulários abertos preservam seus valores e CAS rejeita revisão obsoleta.
- Legado `/estudio/` preservado, sem alteração do arquivo principal; blob e4a9812ac21b5c977b93e53fe65131b43e23ba85.

## Verificações
- WordPress real: `qa_narrative_timeline_transaction.php`: TOTAL_PASS=40 e ROLLBACK=EXECUTED, incluindo 13 novos testes sobre cenas, cronologia, análise, conflito, personagem, relações e Delta.
- WordPress real: `qa_character_appearances_transaction.php`: TOTAL_PASS=28, ROLLBACK=EXECUTED.
- WordPress real: `qa_manuscript_markers_transaction.php`: TOTAL_PASS=66, ROLLBACK=EXECUTED.
- PHP 8.3 lint limpo e dois contratos Python de story-domain e narrativa OK.
- Parser V8 validou sintaxe dos quatro JavaScripts modificados; QA_MANIFEST_PREFLIGHT=PASS 761/761.
- CDN versionado: quatro scripts públicos servidos com hashes exatamente iguais aos novos arquivos do GitHub; /studio/ HTTP200, /estudio/ HTTP200.
- Antes da publicação: hash origem/destino CAS dos 5 arquivos, backup privado e substituição por rename de arquivo temporário. Backup em `/home/u566597497/domains/anthares.us/studio-private-backups/20261122-entity-sync-pr405/`.

## Hashes do código instalado
- `assets/estudio.js`: b6cc1faa7ee8cdd7032ce47ad11153605539acd9
- `assets/studio-character-appearances.js`: 307b570355abac5546e555bae002479df7f3ec5d
- `assets/studio-g7-workspaces.js`: eeb62bb51b1862f115eb0d3f38ba1662079e009a
- `assets/studio-narrative-timeline.js`: 9dbbbe8f1907cbc2c0e2df97b82f98f1dadae55a
- `includes/domain/class-anst-story-domain.php`: dee774ee3e384616adcb18ee3d267af8d9a038e4

## Pendência
- Item 21 da lista selecionada: QA visual autenticado em mais de uma conta e em celular, incluindo edição simultânea e reação dos formulários.
- Documentos do usuário atualizados mantendo os nomes exatos originais `PENDÊNCIAS.md` e `PENDÊNCIAS URGENTES.md`; arquivos entregues no chat.