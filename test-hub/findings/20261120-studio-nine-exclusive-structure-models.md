# Anthares Studio — 9 modelos narrativos exclusivos + régua universal de 3 atos

**Data:** 20/11/2026 (America/Campo_Grande)  
**Situação:** implementado na Hostinger, integrado a `main`, testes transacionais reais aprovados.

## Regra autoral confirmada

Cada projeto possui **uma estrutura principal ativa**, escolhida pelo autor. Os modelos disponíveis são:

1. Estrutura em três atos (3 etapas), com o diagrama detalhado da ação ascendente, incidentes, duas viradas, ponto médio, crise, clímax e desfecho.
2. Jornada do Herói (12 etapas).
3. Pirâmide de Freytag (5 movimentos).
4. A Promessa da Virgem, de Kim Hudson (13 momentos).
5. Círculo da História, de Dan Harmon (8 momentos).
6. Curva de Fichte (6 macro-momentos, permitindo várias crises em cada um).
7. Folha de ritmo Save the Cat!, de Blake Snyder (15 beats).
8. Estrutura narrativa de sete pontos (7 pontos).
9. Kishōtenketsu (4 partes).

A dupla referência “Três atos / Estrutura em três atos” do pedido designa **um mesmo modelo**, apresentado de duas formas. O diagrama detalhado aparece quando esse modelo é escolhido; a régua 25%–50%–25%, com os pontos de virada de 25% e 75%, continua visível na linha do tempo e no gráfico de tensão, qualquer que seja o modelo ativo. As porcentagens dos marcos dos demais modelos são **orientativas**; a equivalência dos dois limites de atos é uma interpretação útil para planejamento e não altera os limites teóricos próprios das estruturas.

### Cruzamento dos modelos com os dois limites dos atos

| Modelo | Região do primeiro limite (25%) | Região do segundo limite (75%) |
|---|---|---|
| Três atos | Ato I | Ato II |
| Jornada do Herói | Travessia do limiar | Caminho de volta |
| Freytag | Ascensão | Queda |
| Promessa da Virgem | Vestir o papel | Travessia solitária |
| Círculo da História | Parte | Retorna |
| Fichte | Primeira escalada | Crise decisiva |
| Save the Cat! | Entrada no segundo ato | Tudo está perdido |
| Sete pontos | Primeira virada | Segunda virada |
| Kishōtenketsu | Ki | Ten |

O sistema apresenta cada correspondência como **aproximação de localização**, preservando a forma e o desenvolvimento particular de cada modelo. O clímax original de Freytag permanece central, diferentemente dos modelos cujo clímax está próximo do encerramento.

## Segurança de dados e fluxo

- Metadado privado `_anst_narrative_selected_model_v1` por projeto, com token de revisão e mutex por usuário/projeto. Seleção persistente via `GET/POST /narrative/structures`.
- O modelo ativo é exposto na leitura do projeto. Alterações de capítulo/cena exigem compatibilidade com o modelo ativo e pertencimento ao mesmo autor.
- A classificação pré-existente dos outros modelos continua preservada para reativação posterior, inclusive após troca de modelo. IDs dos capítulos, cenas e acontecimentos originais permanecem estáveis.
- O Manuscrito continua permitindo criação livre de capítulos; o aviso **Fora da estrutura** e o seletor local aparecem apenas quando existe ao menos um capítulo classificado no modelo ativo.
- Cenas dramatizadas e acontecimentos resumidos podem estar no mesmo capítulo e em etapas diferentes. A linha do tempo conserva as duas ordenações distintas, conforme o trabalho nos itens 8–9.
- Exportação do projeto guarda o modelo selecionado, e a restauração recupera também as associações históricas por um endpoint autenticado com revisão otimista.
- A régua 25%–50%–25% é uma **visualização permanente**, sem ativar o modelo de Três Atos concomitantemente aos demais. Não foi acrescentado um terceiro modo de comparação das duas cronologias.

## Código e implantação

- PR principal: https://github.com/UniversoAnthares/anthares-wordpress/pull/397 — merge `c95a062737161d2cfbc3f1daa2958aa7c0d41b72`.
- PR da regressão antiga: https://github.com/UniversoAnthares/anthares-wordpress/pull/398 — merge `ea825007926645120bd7219bff5666564503d7a0`.
- `anthares-studio/includes/domain/class-anst-structure-models.php` `656b21196c4bb53fdb65acf36df81ff483e3e5ea`
- `anthares-studio/assets/studio-structure-models.css` `d6c755b2d801106cdbc36213f8100928d5e1eca6`
- `anthares-studio/includes/domain/class-anst-narrative-timeline.php` `e2b5bd5b9fe008702f5f32f5b29dae94d72bc886`
- `anthares-studio/assets/studio-narrative-timeline.js` `432270ff5f41c87380edc52f83384f71c5b59f13`
- `anthares-studio/assets/estudio.js` `38059d270e4771374ef8a9bf7b76c76be0bf157e`
- `anthares-studio/anthares-estudio.php` `17aee363947ac9064a5cee9bd6281e664918cb99`
- Backups privados dos quatro arquivos modificados em `/home/u566597497/domains/anthares.us/studio-private-backups/20261120-exclusive-models-v3`, fora de `public_html`. Novos arquivos instalados somente após verificação do hash e inexistência do destino.
- Todos os seis arquivos implantados com SHA idêntico ao GitHub e substituição atômica dentro do mesmo filesystem; rollback previsto em caso de falha.
- `/studio/`, `/estudio/`, JS e CSS retornaram HTTP 200; plugin ativo.

## QA

- `anthares-studio/tests/qa_structure_models_transaction.php`: **46/46 PASS** (todos os nove modelos e seus cruzamentos, exclusividade, alterações sequenciais, conflito de revisão, preservação e restauração, bloqueio de outras contas, modelo nas cenas, vínculos/IDs preservados).
- `anthares-studio/tests/qa_narrative_timeline_transaction.php`: **27/27 PASS**, regressão completa dos itens 8–9 ajustada à regra exclusiva.
- Total: **73/73** em WordPress real, com `START TRANSACTION`/`ROLLBACK`, nenhum registro de teste mantido.
- PHP 8.3 `-l` e JavaScript `node --check` aprovados.
- Manifestos QA iguais, cobertura 743/743 fontes auditáveis, sem faltantes nem duplicatas.

**Pendente específico de aceite:** homologação visual com conta autenticada, navegação por teclado e arraste real entre os modelos, em diferentes telas e tamanhos, no escopo do item 21.

## Referências consultadas para os nomes e percursos

- Kim Hudson, relação original dos 13 momentos: https://kehudson.wordpress.com/2011/01/05/a-new-structure-scriptshark-guest-blog/
- Discussão comparativa de três atos, Freytag, Kishōtenketsu, Fichte e Save the Cat: https://scenaloom.com/guides/story-structure
- Pirâmide original de Freytag em cinco movimentos: https://reedsy.com/blog/guide/story-structure/freytags-pyramid/
