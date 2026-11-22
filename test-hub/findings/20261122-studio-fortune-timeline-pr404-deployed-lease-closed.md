# Anthares Studio — Desgraça na linha do tempo e escala da Tensão

**Data:** 22/11/2026 (America/Campo_Grande)
**Resultado:** código implantado na Hostinger e QA de domínio aprovado. Homologação visual autenticada continua no item 21.
**Lease:** `test-hub/findings/lease-studio-fortune-timeline-20261122.md`; STATUS `CLOSED_SUCCESS`.
**Repositório:** `UniversoAnthares/anthares-wordpress` PR #404; merge `04a69560709345cc1659dce1b623844fd8401276`.

## Alterações
- Tensão limita escolha a -1, +1; Desgraça permite inteiros -5..+5 inclusive 0.
- Campo `descricao` opcional de até 1000 caracteres somente para `desgraca`, disponível em ACF/REST; fechamento do modal após inserção preserva post e tag Quill.
- Ficha da marcação editável no manuscrito e pela linha do tempo; atualização exclusiva da descrição preserva as posições compiladas.
- Régua da linha do tempo de apresentação exibe os pontos de Desgraça proporcionais aos caracteres; a cronologia diegética permanece independente.
- Ritmo e Estilo não recebem o modal, nem os pontos correspondentes; servidor recusa descrições nesses tipos.
- Restaurar backup v6 com tensão +/-3 converte amplitude para +/-1 mantendo o sinal; dados privados remapeados.
- Documentação existente `anthares-studio/docs/MARCADORES_QUILL_GRAFICOS_IMPL_v1.md` atualizada sem renomear.

## Homologação
- WordPress real: 66/66 testes de marcadores e recuperação, `ROLLBACK=EXECUTED`.
- Regressão de cronologia e Jornada: 27/27, `ROLLBACK=EXECUTED`.
- 12/12 testes de contrato Python, lint PHP 8.3 e parser V8 dos três JS aprovados.
- Três cenários funcionais de apresentação dos pontos de Desgraça aprovados em memória.
- QA_MANIFEST_PREFLIGHT=PASS: 761/761 arquivos auditáveis atribuídos uma única vez.
- HTTP 200 para `/studio/` e `/estudio/`. JS/CSS versionados `?ver=` entregam a nova versão; URLs sem query podem apresentar cache antigo por CDN.
- Todos os seis arquivos de execução tiveram hash prévio confirmado antes de substituição, backup privado e escrita atômica.
- Legado `/estudio/` sem alteração; hash original `e4a9812ac21b5c977b93e53fe65131b43e23ba85`.

## Hashes de arquivos implantados (Git blobs)
- `assets/estudio.js`: `3bbb2f08e6195399f324b018827413030a7aa620`
- `assets/studio-manuscript-markers.css`: `ba9266723532b384f46f7735f524b93cfc03d50d`
- `assets/studio-manuscript-markers.js`: `a6f5169ed0a407342f5583662b5ca7406a46718a`
- `assets/studio-narrative-timeline.css`: `eb707cd7dee24d6920e8ef5e6de4ad096c37d7f2`
- `assets/studio-narrative-timeline.js`: `50df0bc1ea236a8fcdd18420ba7c100fb93ab319`
- `includes/domain/class-anst-manuscript-markers.php`: `270932302c144356253a2e02cb32bef6c414c0b8`
- Backup: `/home/u566597497/domains/anthares.us/studio-private-backups/20261122-fortune-timeline-pr404/`.

## Pendências remanescentes
- Item 21: homologação visual autenticada de mouse, teclado e mobile.
- Gráfico de Estilo ainda sem métricas, e migração opcional do `aestDiscourse` para marcadores de Ritmo.
- O item 10 possui código implantado e testes de domínio aprovados, sem exigir dois marcadores livres iniciais; essa regra foi substituída pelo briefing de 22/11/2026.