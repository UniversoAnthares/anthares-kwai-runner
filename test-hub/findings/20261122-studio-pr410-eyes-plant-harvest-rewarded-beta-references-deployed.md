# Anthares Studio — PR #410, itens urgentes 12, 16, 19 e 20

Data: 2026-11-22, fuso America/Campo_Grande.
Owner: ChatGPT/STUDIO_URGENT_20261122.
Lease: test-hub/findings/lease-studio-urgent-features-20261122.md. Estado: CLOSED_SUCCESS (código implantado; pendências declaradas).
Canonical repo: UniversoAnthares/anthares-wordpress, branch main, PR #410 merged as 6eb9b57da4ecf557ac861728866002490f2e202b.

## Implementações
- Item 12: controles de olho nos sete grupos navegáveis do Planejamento; preferências por projeto, recuperação de dados, cálculo do percentual a partir dos campos preenchidos pelo servidor, em Visão geral e Planejamento.
- Item 19: tipos de marcador privados plantar/colher, inserção independente em qualquer sequência, vínculo recíproco exclusivo e reversível por ID de marcador e revisão, gráfico vermelho pendente e verde vinculado, salto para manuscrito e '?' explicativo. Legacy aestPista preservado para leitura.
- Item 20: links por identidade ACF para personagem/lugar/grupo/regra/evento/cena/beat/conflito/fonte, registro inline no Quill, ocorrências nas fichas e gráfico com links por posição, nova CPT privada anst_regra (enunciado/âmbito/exceções).
- Item 16: convite beta oferece valor imutável de Runas ou reais (reais persistidos em centavos), leitor envia sugestão, autor aceita/recusa, revisão e propriedade protegidas; aceitação gera status awaiting_payment. **NENHUMA TRANSFERÊNCIA DE RUNAS OU DINHEIRO FOI IMPLEMENTADA OU REALIZADA**: adaptador atual é somente leitura.
- Contrato documental atualizado in place: anthares-studio/docs/MARCADORES_QUILL_GRAFICOS_IMPL_v1.md.
- O /estudio/ legado foi preservado (hash e4a9812ac21b5c977b93e53fe65131b43e23ba85).

## QA real e publicação
- PHP 8.3 lint: seis arquivos PHP, incluindo QA.
- Contracts: test_manuscript_markers_contract.py 12/12; test_g7_story_domain.py 21/21; test_narrative_timeline_contract.py 9/9.
- JavaScript parser V8: 3/3 scripts alterados.
- QA inventory: 761/761 assigned exactly once.
- WordPress real via WP CLI em transação InnoDB: 77/77 marcadores, 51/51 cronologia/identidade/planejamento/leitura beta, 28/28 aparições de personagens. Todos concluíram com ROLLBACK=EXECUTED. TOTAL=156 verificações.
- Deploy CAS: 9 arquivos antes de publicar tinham hash GitHub main 982297f5..., backups privados preservados em /home/u566597497/domains/anthares.us/studio-private-backups/20261122-studio-urgent-pr410; troca atômica por arquivo + rollback no erro.
- CDN validado com query de versão: 5 ativos CSS/JS têm hashes iguais aos blobs do PR; /studio/ HTTP 200 e /estudio/ HTTP 200.

## Limites ainda pendentes
- Item 16: integrar carteira/ledger existente de Runas e pagamentos reais com liquidação confiável, idempotência e controle de duplicidade; comentários lineares ancorados como Google Docs, enquetes e QA visual multiaccount.
- Item 20: mapa geográfico interativo, rotas/distâncias e calendários; conciliação de elementos antigos não ACF; QA visual de salto exato.
- Item 12: o UI atualmente tem sete agrupamentos navegáveis, 11 etapas pedagógicas subjacentes; QA visual, móvel e teclado.
- Item 19: QA visual de novos marcadores nas interfaces; coexistência de documentos legados.
- Item 23: QA autenticado final, móvel e de concorrência. Status de entrega é **production code + rollback QA**, sem alegação de teste manual visual com conta real.
