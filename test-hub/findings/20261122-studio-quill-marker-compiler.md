# Anthares Studio — marcadores Quill persistentes, compilação sob demanda e gráficos

**Implantado:** 22/11/2026 (America/Campo_Grande)  
**Repositório:** `UniversoAnthares/anthares-wordpress`  
**PR e revisão integrados:** https://github.com/UniversoAnthares/anthares-wordpress/pull/402 · `a2d712550c36bccb498fca04a5be305d81655d0b`  
**Fonte autorizada:** `ANTHARES_STUDIO_ESPECIFICACAO_MARCADORES_QUILL_E_GRAFICOS_v1.md` (21/11/2026).  
**Log de implementação:** `anthares-studio/docs/MARCADORES_QUILL_GRAFICOS_IMPL_v1.md` na branch principal.

## Implementado no WordPress em produção

1. Novo tipo de post privado `anst_marcacao`, com grupo ACF `group_anst_marker_v1` e campos de tipo, valor, personagem, entrada vinculada, projeto, capítulo, posição, versão e estado. As posições de cada novo marcador começam em `-1`; IDs de posts permanecem estáveis.
2. Novo Quill 2.x `EmbedBlot` `aestMarcador`, com atributos `data-tipo`, `data-id`, `data-valor`, `data-personagem`, sem substituir os blots `aestEntity`, `aestPista`, `aestDiscourse`.
3. Controles de inserção no Manuscrito: tensão e desgraça `-3,-1,+1,+3`; ritmo `dialogo`, `acao`, `sumario_narrativo`, `descricao`; entrada e saída de personagem, com seleção/criação de ficha somente do mesmo projeto. Saída exige uma entrada anterior aberta, vinculada pelo ID específico.
4. Criação idempotente; confirmação pelo salvamento do Delta Quill; edição posterior de valor mantém o post original e sincroniza o Delta do capítulo no mesmo bloqueio de gravação com proteção de hash/revisão.
5. Compilador por clique: varre os Deltas armazenados, conta pontos de código Unicode (espaços/quebras incluídos), ignora a extensão gráfica dos embeds, preserva índice Quill UTF-16 e calcula posição local e cumulativa da obra conforme a ordem do Manuscrito. Reconcilia duplicações, ausências, divergências e saídas órfãs; marca gráfico desatualizado ao editar.
6. Quatro gráficos nativos SVG em Análises: tensão e desgraça cumulativas, ritmo proporcional aos caracteres e Gantt de personagens, com pares entre capítulos e recorte por capítulo. Sinalização de saída órfã com ponto vermelho forte e ausência da barra; outras cores pastéis. Tabela acessível e links ao trecho do capítulo.
7. Ferramentas antigas de linha do tempo e Jornada permanecem. Metadados e identificações anteriores de personagens são mantidos como sistemas separados para impedir dupla contagem automática.
8. Exportação TXT/HTML omite os embeds. DOCX utiliza a extração textual. Exportação estruturada JSON v6 inclui marcadores privados; restauração idempotente remapeia IDs de capítulos, fichas de personagens, marcadores, Deltas e histórico.
9. CPT e REST são privados: bloqueio de leitura/escrita entre contas e entre projetos/capítulos, verificação de tipo e atributos mesmo se manipulados no Delta, proteção de revisão e mutex de salvamento.

## Evidência de implantação

Cinco arquivos instalados por substituição atômica após preflight SHA; duas versões anteriores guardadas em backups privados fora de `public_html`:

`/home/u566597497/domains/anthares.us/studio-private-backups/20261122-manuscript-markers-v1/`

| Arquivo | SHA do arquivo em `main` e produção |
|---|---|
| `anthares-studio/includes/domain/class-anst-manuscript-markers.php` | `30836f188b47e709c271f0b622ea151726b76dc0` |
| `anthares-studio/assets/studio-manuscript-markers.js` | `89b2647f9d92913d669e59e3166b9f371c022c89` |
| `anthares-studio/assets/studio-manuscript-markers.css` | `7f8738773349dda201129dfcbf58edcbe5dab78f` |
| `anthares-studio/assets/estudio.js` | `6750710ea73121738b00cbf228853849bfaf9037` |
| `anthares-studio/anthares-estudio.php` | `600f2a527ac3a2bd1635bab45cb6f4ffb97c82af` |

Verificações após a instalação:

- **50/50 PASS**: `qa_manuscript_markers_transaction.php` executado na instalação WordPress real, com `ROLLBACK=EXECUTED`; nenhum registro QA retido.
- **27/27 PASS**: regressão transacional real de `qa_narrative_timeline_transaction.php`, preservando os itens 8 e 9.
- **8/8 PASS**: contrato estático de Quill/CPT/restauração/gráficos.
- PHP 8.3 `-l` PASS para módulo e plugin. Node `--check` PASS para ambos os scripts principais.
- Todos os endpoints REST previstos registrados; CPT `anst_marcacao` e grupo ACF registrados, plugin WordPress ativo.
- `/studio/`, `/estudio/`, JS e CSS novos: HTTP 200.
- Manifestos QA idênticos cobrindo 759 arquivos auditáveis, sem ausências ou duplicações.

## Decisões explicitamente provisórias

Para preencher escolhas deixadas abertas no documento v1, foi usada soma cumulativa partindo de zero, em que sinais positivos de `desgraca` indicam **melhoria da sorte**; sinais negativos indicam **piora**, de acordo com o material pedagógico. O Gantt de personagem com entrada sem saída assume permanência até o fim do recorte; o último ritmo permanece até o final do texto. Gráficos são SVG nativos, sem biblioteca externa.

**Permanece pendente:** gráfico de **Estilo**, sem categorias/indicadores definidos; decisão sobre dois pontos livres iniciais do editor pedagógico anterior da Curva da Desgraça e eventual migração explícita, nunca silenciosa, de marcadores existentes; homologação visual completa com conta autenticada, mouse, teclado, telas móveis, no item 21. Testes de domínio/REST e hashes de produção não substituem a homologação visual.

**Situação de engenharia:** publicados CPT, Quill, compilador e os quatro gráficos; as decisões editoriais pendentes foram documentadas em separado.
