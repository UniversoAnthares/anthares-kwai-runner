# Anthares Studio — auditoria individual dos 188 requisitos
STATUS: PROVEN (rastreabilidade estática de todos os 188 itens)
AREA: studio/requirements-audit
DATE: 2026-11-19
RUN: leitura do código GitHub PR #342
JOB: https://github.com/UniversoAnthares/anthares-wordpress/pull/342
COMMIT: e83586c7d1887c9b307a7810881e0e61a396ccc4
SUPERSEDES: none

## Natureza e limite da prova

Auditoria individual **de cobertura de código e requisitos** concluída para as 188 entradas do documento `especificacao_atualizada.md` (13/11/2026). Todos os IDs 001–188 possuem diagnóstico específico e possível referência de código. Os marcadores FOUND significam **existência de assinatura explícita no código**; funcionalidade pronta requer teste de execução separado. PARTIAL indica que foi encontrada alguma implementação relacionada, com requisitos adicionais ainda não comprovados. GATED identifica domínio narrativo dependente da ativação ACF. NO_EVIDENCE indica falta de prova específica localizada nesta busca, sem conclusão de inexistência absoluta. EXCLUDED corresponde à decisão posterior de retirar leitura beta do escopo interno. O documento respeita a distinção entre inspeção estática e homologação com contas reais.

A auditoria utiliza a branch feat/studio-chapter-history-export-20261119, commit e83586c7d1887c9b307a7810881e0e61a396ccc4. A versão implantada do JavaScript foi verificada como equivalente a essa branch na rodada anterior. **Nenhuma gravação nem alteração de autorização foi realizada nesta auditoria.** Validação funcional individual, dispositivos móveis, restauração integral e permissões entre duas contas continuam nas tarefas próprias.

## Resumo verificável

- Requisitos listados: 188; IDs distintos: 188.
- Assinatura específica localizada (FOUND): 45.
- Implementação relacionada, cobertura incompleta (PARTIAL): 88.
- Domínio dependente de homologação ACF (GATED): 35.
- Sem prova específica encontrada (NO_EVIDENCE): 17.
- Retirados do escopo interno por decisão posterior (EXCLUDED): 3.
- Soma de classificações: 188.
- Gate ACF conferido em `class-anst-story-domain.php`: SIM.
- Confronto exato de âncoras sem correspondente: 1 (042 js: audience).

## Fontes de implementação consultadas

- `anthares-studio/assets/estudio.js` — Git blob `92856949868eaeb8ae5928b58e5a65a476f1edd4`.
- `anthares-studio/anthares-estudio.php` — Git blob `97759fdd9f056e923ffca96197221b316d4a7095`.
- `anthares-studio/includes/domain/class-anst-story-domain.php` — Git blob `3f1925e1030fbced05e50d568060d2d0146c5dba`.
- `anthares-studio/includes/domain/class-anst-g7-workspace.php` — Git blob `5aadc41fb7f205c41778a575348ef390873e0894`.
- `anthares-studio/includes/domain/class-anst-g7-impact.php` — Git blob `cc3116cdd821c9872b53b314d7d6f2b84afc49e0`.
- `anthares-studio/includes/domain/class-anst-g7-universes.php` — Git blob `097ee97298adedf16be184a3246e35bfc1969e33`.
- `anthares-studio/includes/domain/class-anst-g7-files.php` — Git blob `8ef8b6be623afece350b55d68edf73b692c84ee1`.
- `anthares-studio/includes/domain/class-anst-g7-docx.php` — Git blob `051e53169a4e8e14e924b27ea15cdecaae951dca`.
- `anthares-studio/includes/domain/class-anst-g7-capture.php` — Git blob `f223661fad241a4762ccd923ee13eb2441031eae`.
- `anthares-studio/includes/domain/class-anst-g7-beta.php` — Git blob `047d04466002193121b0bd62e02fd731d8e4bf41`.
- `anthares-studio/includes/domain/class-anst-g7-mentors.php` — Git blob `6a1c8f0bf993c86a6ff93740f37296394458a55e`.

## Matriz de rastreabilidade (um registro por requisito)

| ID | Classe | Requisito textual | Evidência estática / Estado | Arquivo e âncora |
|---:|---|---|---|---|
| 001 | P0·T | Criar projeto sem ideia definida. | FOUND | `anthares-studio/assets/estudio.js:2148` (`function createProject(`) |
| 002 | P0·T | Escolher o ponto de partida. | FOUND | `anthares-studio/assets/estudio.js:263` (`function startCards(`) |
| 003 | P0·T | Múltiplos projetos independentes. | FOUND | `anthares-studio/anthares-estudio.php:540` (`function anst_bootstrap(`) |
| 004 | P0·T | Painel único do projeto. | FOUND | `anthares-studio/assets/estudio.js:1638` (`function renderProject(`) |
| 005 | P0·T | Navegação por áreas permanentes. | FOUND | `anthares-studio/assets/estudio.js:471` (`const projectGroups=`) |
| 006 | P0·E | Salvamento automático e sincronização. | PARTIAL | `anthares-studio/assets/estudio.js:2098` (`function queueSave(`) |
| 007 | P0·E | Histórico de versões recuperáveis. | PARTIAL | `anthares-studio/anthares-estudio.php:1400` (`function anst_version_manage(`) |
| 008 | P0·T | Arquivo central de materiais. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-files.php:51` (`function anst_g7_file_upload(`) |
| 009 | P1·T | Busca global. | PARTIAL | `anthares-studio/assets/estudio.js:376` (`function renderStudioSearch(`) |
| 010 | P1·T | Etiquetas e coleções próprias. | NO_EVIDENCE | - |
| 011 | P1·E | Subprojetos e compartilhamento de universo. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-universes.php:61` (`function anst_g7_universe_link(`) |
| 012 | P1·E | Modos de trabalho. | FOUND | `anthares-studio/assets/estudio.js:31` (`function applyWritingFocus(`) |
| 013 | P1·E | Registro de decisões. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:238` (`function anst_g7_history(`) |
| 014 | P0·D | Caixa de captura de ideias. | FOUND | `anthares-studio/anthares-estudio.php:592` (`function anst_create_note(`) |
| 015 | P0·D | Brainstorm livre. | FOUND | `anthares-studio/assets/estudio.js:673` (`function muralMarkup(`) |
| 016 | P0·T | Brainstorm guiado. | PARTIAL | `anthares-studio/assets/estudio.js:814` (`function renderUnlock(`) |
| 017 | P0·D | Agrupamento de ideias. | FOUND | `anthares-studio/assets/estudio.js:626` (`function boardCols(`) |
| 018 | P0·D | Mural visual reorganizável. | FOUND | `anthares-studio/assets/estudio.js:790` (`function cardMove(`) |
| 019 | P0·T | Criar elementos narrativos a partir de notas. | PARTIAL | `anthares-studio/anthares-estudio.php:519` (`function anst_board_import(`) |
| 020 | P0·D | Pesquisa técnica. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:9` (`function anst_g7_kinds(`) |
| 021 | P0·D | Pesquisa investigativa. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:9` (`function anst_g7_kinds(`) |
| 022 | P1·D | Pesquisa ficcional. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:9` (`function anst_g7_kinds(`) |
| 023 | P1·D | Pesquisa experimental/ativa. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:9` (`function anst_g7_kinds(`) |
| 024 | P0·T | Fichamento de fontes. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:30` (`source_`) |
| 025 | P0·T | Acervo de referências visuais e sonoras. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-files.php:51` (`function anst_g7_file_upload(`) |
| 026 | P1·T | Quadro de perguntas em aberto. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:265` (`function anst_g7_progress(`) |
| 027 | P1·T | Biblioteca do gênero. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:9` (`function anst_g7_kinds(`) |
| 028 | P1·T | Fichas de leitura crítica. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:9` (`function anst_g7_kinds(`) |
| 029 | P1·T | Laboratório de combinações. | PARTIAL | `anthares-studio/assets/estudio.js:814` (`function renderUnlock(`) |
| 030 | P1·E | Exercícios de geração de ideias. | PARTIAL | `anthares-studio/assets/estudio.js:814` (`function renderUnlock(`) |
| 031 | P2·E | Assistência opcional para identificar contradições e lacunas. | NO_EVIDENCE | - |
| 032 | P0·D | Formulário de premissa. | FOUND | `anthares-studio/assets/estudio.js:1669` (`['premise','Premissa'`) |
| 033 | P0·D | Editor de logline. | FOUND | `anthares-studio/assets/estudio.js:552` (`function sentenceEditor(`) |
| 034 | P0·D | Editor de storyline. | FOUND | `anthares-studio/assets/estudio.js:552` (`function sentenceEditor(`) |
| 035 | P0·D | Tema principal. | PARTIAL | `anthares-studio/assets/estudio.js:1672` (`['theme','Tema'`) |
| 036 | P0·D | Temas secundários. | NO_EVIDENCE | - |
| 037 | P0·D | Tese/ideia governante. | FOUND | `anthares-studio/assets/estudio.js:1673` (`['thesis','Tese'`) |
| 038 | P0·D | Tom principal e variações. | PARTIAL | `anthares-studio/anthares-estudio.php:300` (`function anst_project_tone(`) |
| 039 | P0·D | Emoção-chave e unidade de efeito. | NO_EVIDENCE | - |
| 040 | P0·T | Conflito central. | PARTIAL | `anthares-studio/assets/estudio.js:511` (`obstacle`) |
| 041 | P1·T | Pacto de gênero e expectativa. | PARTIAL | `anthares-studio/assets/estudio.js:352` (`genre`) |
| 042 | P1·T | Público imaginado e experiência de leitura desejada. | NO_EVIDENCE | - |
| 043 | P0·T | Comparação das versões do conceito. | NO_EVIDENCE | - |
| 044 | P0·T | Síntese automática de campos já preenchidos. | FOUND | `anthares-studio/assets/estudio.js:1624` (`function renderConceptSynthesis(`) |
| 045 | P1·T | Alertas de desalinhamento. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-impact.php:8` (`function anst_g7_impact_report(`) |
| 046 | P0·D | Quadro de cartões ilimitados. | FOUND | `anthares-studio/assets/estudio.js:631` (`function boardCard(`) |
| 047 | P0·D | Reordenação por arrastar e soltar. | FOUND | `anthares-studio/assets/estudio.js:790` (`function cardMove(`) |
| 048 | P0·D | Ligações de causa e consequência. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:224` (`function anst_story_relations(`) |
| 049 | P0·D | Outline em tópicos. | PARTIAL | `anthares-studio/assets/estudio.js:48` (`outline`) |
| 050 | P0·D | Expansão progressiva. | FOUND | `anthares-studio/assets/estudio.js:814` (`function renderUnlock(`) |
| 051 | P0·D | Hierarquia ato → sequência → cena → beat. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:8` (`function anst_story_types(`) |
| 052 | P0·D | Estrutura em três atos. | FOUND | `anthares-studio/assets/estudio.js:1042` (`three_acts`) |
| 053 | P0·D | Pontos de virada e clímax. | PARTIAL | `anthares-studio/assets/estudio.js:511` (`turning`) |
| 054 | P1·D | Modelos alternativos. | FOUND | `anthares-studio/assets/estudio.js:1046` (`hero_journey`) |
| 055 | P1·D | Assistente Snowflake. | NO_EVIDENCE | - |
| 056 | P1·T | Modelos combináveis e personalizáveis. | PARTIAL | `anthares-studio/assets/estudio.js:1041` (`structureModels`) |
| 057 | P0·T | Subtramas independentes. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:12` (`conflito`) |
| 058 | P0·T | Visualização por linha narrativa. | PARTIAL | `anthares-studio/assets/estudio.js:1097` (`function renderStructure(`) |
| 059 | P0·T | Linha temporal de fatos. | GATED | `anthares-studio/assets/estudio.js:1063` (`function renderNarrativeChronology(`) |
| 060 | P1·T | Flashbacks, flashforwards e paralelismo. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`story_time`) |
| 061 | P0·T | Lacunas de ligação. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-impact.php:8` (`function anst_g7_impact_report(`) |
| 062 | P0·D | Estrutura de cena. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:15` (`function anst_story_fields(`) |
| 063 | P1·D | Cenas proativas e reativas. | NO_EVIDENCE | - |
| 064 | P1·T | Beats internos da cena. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:11` (`beat`) |
| 065 | P1·T | Planejador de reviravoltas. | NO_EVIDENCE | - |
| 066 | P1·D | Plant/Payoff e pistas falsas. | PARTIAL | `anthares-studio/assets/estudio.js:1919` (`mark-pista`) |
| 067 | P1·T | História causal em grafo. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:224` (`function anst_story_relations(`) |
| 068 | P1·E | Cenários estruturais alternativos. | PARTIAL | `anthares-studio/assets/estudio.js:1041` (`structureModels`) |
| 069 | P0·D | Ficha e perfil de personagem. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:10` (`personagem`) |
| 070 | P0·D | Papel na história. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`role`) |
| 071 | P0·D | Arquétipos opcionais. | NO_EVIDENCE | - |
| 072 | P0·D | Desejo, necessidade, motivação e objetivo. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`objective`) |
| 073 | P0·D | Obstáculos, riscos e perdas possíveis. | NO_EVIDENCE | - |
| 074 | P0·D | Passado relevante e 'fantasma'. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`attributes_json`) |
| 075 | P0·D | Personalidade, temperamento e caráter. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`attributes_json`) |
| 076 | P1·D | Falha moral, contradição, segredo, crença e autoimagem. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`attributes_json`) |
| 077 | P1·D | Aparência, marcas, maneirismos, hábitos e linguagem. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`attributes_json`) |
| 078 | P0·D | Arco de transformação. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`arc_json`) |
| 079 | P1·D | Arcos do antagonista e dos secundários. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`arc_json`) |
| 080 | P0·D | Relações direcionais. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:224` (`function anst_story_relations(`) |
| 081 | P1·T | Mapa visual das relações. | PARTIAL | `anthares-studio/assets/estudio.js:1208` (`function renderStoryEntities(`) |
| 082 | P1·T | Linha de participação do personagem. | GATED | `anthares-studio/assets/estudio.js:1063` (`function renderNarrativeChronology(`) |
| 083 | P1·D | Planejador de apresentação. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`attributes_json`) |
| 084 | P1·D | Guia individual de voz. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`voice`) |
| 085 | P1·D | Entrevista com o personagem. | NO_EVIDENCE | - |
| 086 | P1·E | Consistência de decisão. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-impact.php:8` (`function anst_g7_impact_report(`) |
| 087 | P1·T | Dossiê de personagem exportável. | FOUND | `anthares-studio/assets/estudio.js:1175` (`function exportStoryDossier(`) |
| 088 | P0·D | Fichas de locais e cenários. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:10` (`lugar`) |
| 089 | P0·D | Fichas de povos, culturas e grupos. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:10` (`grupo`) |
| 090 | P0·D | Enciclopédia do projeto. | PARTIAL | `anthares-studio/assets/estudio.js:986` (`function renderElements(`) |
| 091 | P0·T | Regras e limites do universo. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`rules_json`) |
| 092 | P0·T | Linha histórica do universo. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`history`) |
| 093 | P0·T | Calendário e datas internas. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`story_time`) |
| 094 | P1·D | Cartografia. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`map_refs_json`) |
| 095 | P1·T | Distâncias e deslocamentos. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`map_refs_json`) |
| 096 | P1·D | Geografia e recursos naturais. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`culture_json`) |
| 097 | P1·D | Civilizações e estrutura social. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`culture_json`) |
| 098 | P1·D | Economia. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`culture_json`) |
| 099 | P1·D | Governo, política e legislação. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`rules_json`) |
| 100 | P1·D | Religiões e cosmogonias. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`culture_json`) |
| 101 | P1·D | Idiomas e nomes próprios. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`culture_json`) |
| 102 | P1·D | Magia e sistemas extraordinários. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:18` (`rules_json`) |
| 103 | P1·T | História das facções. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-universes.php:164` (`function anst_g7_universe_library(`) |
| 104 | P1·T | Relação universo → conflito → cena. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:224` (`function anst_story_relations(`) |
| 105 | P1·E | Alertas de continuidade espacial e temporal. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-impact.php:8` (`function anst_g7_impact_report(`) |
| 106 | P2·E | Gerador/cartógrafo opcional. | NO_EVIDENCE | - |
| 107 | P0·T | Editor de texto com capítulos e cenas. | FOUND | `anthares-studio/assets/estudio.js:1875` (`function renderManuscript(`) |
| 108 | P0·E | Escrita sem distrações. | FOUND | `anthares-studio/assets/estudio.js:31` (`function applyWritingFocus(`) |
| 109 | P0·T | Painel de referência durante a escrita. | FOUND | `anthares-studio/assets/estudio.js:37` (`function updateWritingReferences(`) |
| 110 | P0·T | Sincronização entre outline e manuscrito. | PARTIAL | `anthares-studio/anthares-estudio.php:381` (`function anst_reorder_chapters(`) |
| 111 | P0·T | Versões e comparação textual. | FOUND | `anthares-studio/assets/estudio.js:1614` (`function reviewCompareDialog(`) |
| 112 | P0·D | Definição de narrador e foco narrativo. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`pov`) |
| 113 | P0·D | Controle de focalização. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`pov`) |
| 114 | P1·T | Escolha de tempo verbal. | NO_EVIDENCE | - |
| 115 | P1·T | Distância narrativa e voz. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:17` (`voice`) |
| 116 | P1·T | Alternância de narrador com marcas visíveis. | PARTIAL | `anthares-studio/assets/estudio.js:1919` (`discourse-mark`) |
| 117 | P1·E | Importação e exportação. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-docx.php:7` (`function anst_g7_docx_parse(`) |
| 118 | P1·E | Contadores e metas. | PARTIAL | `anthares-studio/assets/estudio.js:2097` (`function updateWordCount(`) |
| 119 | P0·D | Ficha completa de cena. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:15` (`function anst_story_fields(`) |
| 120 | P0·D | Função narrativa da cena. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`goal`) |
| 121 | P0·D | Classificação contar/mostrar. | FOUND | `anthares-studio/assets/estudio.js:1919` (`discourse-mark`) |
| 122 | P1·D | Sumarização vs. dramatização. | PARTIAL | `anthares-studio/assets/estudio.js:1919` (`discourse-mark`) |
| 123 | P1·T | Tempo da história vs. espaço narrativo. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`duration_minutes`) |
| 124 | P1·D | Planejamento de diálogos. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`goal`) |
| 125 | P1·D | Subtexto e informação omitida. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`goal`) |
| 126 | P1·T | Revisão por personagem. | PARTIAL | `anthares-studio/assets/estudio.js:1425` (`function renderTextDiagnostics(`) |
| 127 | P1·T | Marcações por personagem e tipo de discurso. | PARTIAL | `anthares-studio/assets/estudio.js:1897` (`entity-link`) |
| 128 | P1·D | Verificador de diálogos expositivos. | PARTIAL | `anthares-studio/assets/estudio.js:1425` (`function renderTextDiagnostics(`) |
| 129 | P1·T | Densidade de diálogo. | FOUND | `anthares-studio/assets/estudio.js:1402` (`function narrativeTextMetrics(`) |
| 130 | P1·D | Revisão de concisão. | FOUND | `anthares-studio/assets/estudio.js:1425` (`function renderTextDiagnostics(`) |
| 131 | P1·D | Pesquisa de adjetivos e advérbios. | FOUND | `anthares-studio/assets/estudio.js:1402` (`function narrativeTextMetrics(`) |
| 132 | P1·E | Consulta contextual de orientações do curso. | PARTIAL | `anthares-studio/assets/estudio.js:595` (`function lessonControls(`) |
| 133 | P1·E | Comentários e tarefas ligados a intervalos de texto. | FOUND | `anthares-studio/anthares-estudio.php:1267` (`function anst_review_anchor_at(`) |
| 134 | P2·E | Comparador de versões estilísticas. | FOUND | `anthares-studio/assets/estudio.js:1614` (`function reviewCompareDialog(`) |
| 135 | P0·D | Curva de tensão por cena/beat. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`tension_planned`) |
| 136 | P0·D | Escala de agravamento de conflito. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`conflict_score`) |
| 137 | P0·D | Curva de fortuna/desgraça do protagonista. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`fortune_score`) |
| 138 | P1·T | Curvas individuais de personagens. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`tension_planned`) |
| 139 | P0·T | Gráfico da distribuição de atos, capítulos, sequências e cenas. | PARTIAL | `anthares-studio/assets/estudio.js:1452` (`function renderChapterMetrics(`) |
| 140 | P0·T | Ritmo por extensão de beats e cenas. | PARTIAL | `anthares-studio/assets/estudio.js:1452` (`function renderChapterMetrics(`) |
| 141 | P1·D | Variação do tom. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`tone`) |
| 142 | P1·T | Emoção pretendida vs. realizada. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`tension_perceived`) |
| 143 | P1·T | Revelações, pistas e antecipações. | PARTIAL | `anthares-studio/assets/estudio.js:1919` (`mark-pista`) |
| 144 | P1·T | Identificação de longos trechos de baixa transformação. | PARTIAL | `anthares-studio/assets/estudio.js:1425` (`function renderTextDiagnostics(`) |
| 145 | P1·T | Diagnóstico de desequilíbrio entre núcleos. | PARTIAL | `anthares-studio/assets/estudio.js:1452` (`function renderChapterMetrics(`) |
| 146 | P1·T | Distribuição das aparições de personagens. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:224` (`function anst_story_relations(`) |
| 147 | P1·T | Densidade de diálogo, descrição e exposição. | FOUND | `anthares-studio/assets/estudio.js:1402` (`function narrativeTextMetrics(`) |
| 148 | P1·T | Mapa de conflitos não resolvidos. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`conflict_score`) |
| 149 | P1·T | Quadro de promessas narrativas. | PARTIAL | `anthares-studio/assets/estudio.js:1919` (`mark-pista`) |
| 150 | P1·T | Filtros para pontos frágeis. | PARTIAL | `anthares-studio/assets/estudio.js:1425` (`function renderTextDiagnostics(`) |
| 151 | P1·E | Comparação planejado × escrito. | PARTIAL | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`tension_perceived`) |
| 152 | P1·E | Diagnóstico explicável, sem nota estética absoluta. | FOUND | `anthares-studio/assets/estudio.js:1425` (`function renderTextDiagnostics(`) |
| 153 | P0·D | Lista de revisão por técnica. | FOUND | `anthares-studio/assets/estudio.js:1567` (`function renderReview(`) |
| 154 | P0·T | Modos separados de autor e revisor. | PARTIAL | `anthares-studio/assets/estudio.js:31` (`function applyWritingFocus(`) |
| 155 | P0·E | Versões protegidas e restauração. | FOUND | `anthares-studio/anthares-estudio.php:1400` (`function anst_version_manage(`) |
| 156 | P1·T | Revisão de coerência causal. | FOUND | `anthares-studio/assets/estudio.js:1542` (`reviewTypes`) |
| 157 | P1·T | Revisão de conhecimento. | FOUND | `anthares-studio/assets/estudio.js:1542` (`reviewTypes`) |
| 158 | P1·T | Revisão de continuidade temporal. | FOUND | `anthares-studio/assets/estudio.js:1542` (`reviewTypes`) |
| 159 | P1·T | Revisão de elementos recorrentes. | FOUND | `anthares-studio/assets/estudio.js:1542` (`reviewTypes`) |
| 160 | P1·T | Pendências com prioridade e localização. | FOUND | `anthares-studio/anthares-estudio.php:1284` (`function anst_review_manage(`) |
| 161 | P1·D | Exposição controlada das ideias a leitores. | EXCLUDED | `anthares-studio/includes/domain/class-anst-g7-beta.php:91` (`function anst_g7_beta_invites(`) |
| 162 | P1·T | Questionário de leitura beta. | EXCLUDED | `anthares-studio/includes/domain/class-anst-g7-beta.php:218` (`function anst_g7_beta_feedback(`) |
| 163 | P1·T | Comparação de interpretação. | EXCLUDED | `anthares-studio/includes/domain/class-anst-g7-beta.php:218` (`function anst_g7_beta_feedback(`) |
| 164 | P1·E | Permissões por projeto. | PARTIAL | `anthares-studio/anthares-estudio.php:181` (`function anst_permission(`) |
| 165 | P0·D | Aulas relacionadas à ferramenta usada. | PARTIAL | `anthares-studio/assets/estudio.js:595` (`function lessonControls(`) |
| 166 | P0·T | Exercícios executados dentro do projeto. | PARTIAL | `anthares-studio/assets/estudio.js:814` (`function renderUnlock(`) |
| 167 | P0·T | Desafios encadeados. | PARTIAL | `anthares-studio/assets/estudio.js:814` (`function renderUnlock(`) |
| 168 | P0·D | Gestão do desafio de 40 textos. | NO_EVIDENCE | - |
| 169 | P1·D | Exercício de premissa/logline/storyline. | FOUND | `anthares-studio/assets/estudio.js:552` (`function sentenceEditor(`) |
| 170 | P1·D | Exercícios de mistura e sorteio. | PARTIAL | `anthares-studio/assets/estudio.js:814` (`function renderUnlock(`) |
| 171 | P1·D | Exercício de estruturas alternativas. | FOUND | `anthares-studio/assets/estudio.js:1041` (`structureModels`) |
| 172 | P1·D | Entrevista com personagem. | NO_EVIDENCE | - |
| 173 | P1·D | Experimento com narrador. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:21` (`pov`) |
| 174 | P1·D | Experimento contar/mostrar/diálogo. | FOUND | `anthares-studio/assets/estudio.js:1919` (`discourse-mark`) |
| 175 | P1·D | Exercícios de restrição estilística. | PARTIAL | `anthares-studio/assets/estudio.js:1425` (`function renderTextDiagnostics(`) |
| 176 | P1·T | Acompanhamento de progresso. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-workspace.php:265` (`function anst_g7_progress(`) |
| 177 | P1·E | Painel de recomendação da próxima ação. | FOUND | `anthares-studio/assets/estudio.js:1935` (`function renderHome(`) |
| 178 | P0·E | Privacidade por padrão. | FOUND | `anthares-studio/anthares-estudio.php:554` (`function anst_create_project(`) |
| 179 | P0·E | Backup verificável. | PARTIAL | `anthares-studio/anthares-estudio.php:1377` (`function anst_version_snapshot(`) |
| 180 | P0·E | Modelo relacional central. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:39` (`function anst_story_register_types(`) |
| 181 | P0·E | Vínculos sem duplicação. | GATED | `anthares-studio/includes/domain/class-anst-story-domain.php:224` (`function anst_story_relations(`) |
| 182 | P1·E | Alertas de impacto de mudanças. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-impact.php:8` (`function anst_g7_impact_report(`) |
| 183 | P1·E | Atalhos para capturas móveis. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-capture.php:8` (`function anst_g7_capture_form(`) |
| 184 | P1·E | Importação de projetos existentes. | PARTIAL | `anthares-studio/anthares-estudio.php:636` (`function anst_import_chapter(`) |
| 185 | P1·E | Exportação integral estruturada. | PARTIAL | `anthares-studio/assets/estudio.js:1804` (`function exportProjectJson(`) |
| 186 | P1·E | Compatibilidade com acessibilidade. | PARTIAL | `anthares-studio/assets/estudio.js:474` (`function projectTabs(`) |
| 187 | P2·E | Auxílio automatizado opt-in. | NO_EVIDENCE | - |
| 188 | P2·E | Painel para tutores/mentores. | PARTIAL | `anthares-studio/includes/domain/class-anst-g7-mentors.php:54` (`function anst_g7_mentor_create(`) |

## Pendências técnicas decorrentes

1. Resolver os itens NO_EVIDENCE mediante implementação ou comprovação explícita de que são atendidos por outro módulo.
2. Completar os itens PARTIAL e testar caminhos de gravação, exclusão, recuperação, importação e exportação.
3. Habilitar o domínio ACF somente após gate de aprovação, migração e testes reais; manter o modo seguro vigente até lá.
4. Verificar as 188 funcionalidades **em execução** em projetos de teste e com autorização adequada, tarefa distinta da rastreabilidade aqui encerrada.
5. Excluir integrações retiradas do escopo em vez de incorporá-las inadvertidamente às prioridades internas.
