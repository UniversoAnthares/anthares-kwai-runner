# Anthares Studio — Item 11: detecção e marcações privadas de personagens

**Data:** 21/11/2026 (America/Campo_Grande)  
**Situação:** implementado, integrado ao `main` do WordPress e publicado na Hostinger; QA transacional aprovado.

## Escopo fiel ao briefing

Fonte: `site-anthares.docx`, trecho “ah, no item 'personagens', nos campos da ficha...” e `PENDÊNCIAS URGENTES.md`, item 11; Plano Mestre B12/B17.

- Nomes, apelidos e etiquetas de identificação da ficha ACF (`aliases_json`) tornam-se sugestões automáticas nos capítulos. A pesquisa respeita fronteiras Unicode e ignora diferença entre maiúsculas/minúsculas.
- Homônimos são apresentados como candidatos ambíguos, sem classificação presumida.
- O autor pode confirmar: **presença**, **menção**, **personagem focalizador** ou **ignorar**. Somente decisões confirmadas alimentam os números apresentados.
- Manualmente, seleciona uma palavra, pronome ou frase no Quill 2.x e aplica o vínculo `aestEntity=personagem:<ID>`, existente no editor. O autor também escolhe a classificação na interface.
- O novo histórico privado da decisão é armazenado no metadado do capítulo `_anst_character_occurrences_v1`. O Delta Quill canônico e a edição pública conservam o texto e omitem o metadado da classificação.
- Alterações no manuscrito disparam nova pesquisa após salvar. Referências com contexto único podem ser reconciliadas após inserções antes do trecho. Trechos removidos ou situações ambíguas são sinalizados para reavaliação. O usuário pode reassociar e excluir decisões.
- A ficha mostra capítulos e quantidades confirmadas por categoria. O gráfico de distribuição, acessível pela Estrutura/Análises, mostra marcas por capítulo e abre o capítulo correspondente.
- Acesso privado com verificação da titularidade do projeto, personagem e capítulo; trava MySQL por capítulo; token de revisão otimista; confirmação por hash do Delta antes de qualquer escrita; limite por capítulo.

## Implementação

PR principal: https://github.com/UniversoAnthares/anthares-wordpress/pull/399 — squash merge `2b8805abc9fb9b1c7af5df7cab34636106e7536b`.  
PR de correção do fluxo manual após salvamento Quill: https://github.com/UniversoAnthares/anthares-wordpress/pull/400 — squash merge `02bccd716cd7f428e35022986e3f0708847cbd97`.

Arquivos em produção, verificados por hash:
- `includes/domain/class-anst-character-appearances.php`: `85e3c8b215ae099575909185b35caf2dade47b5e`.
- `assets/studio-character-appearances.js`: `fca78a03172ecb785b8cdbbdd1f6a477d2170851` (PR #400).
- `assets/studio-character-appearances.css`: `ec33909a2d20260cf449e08f5d58b5714447ee5a`.
- `assets/estudio.js`: `d5c9f7734741d5e924d056fc6d79b88397dac453`.
- `anthares-estudio.php`: `9c37d7e13f25851cb8ebc48a3593992f49e68d19`.

Backups privados externos ao `public_html`: `/home/u566597497/domains/anthares.us/studio-private-backups/20261121-item11-appearances/`; correção adicional em `manual-race/`. As substituições foram feitas após conferência do arquivo original e do hash de origem. `/studio/`, `/estudio/`, JS e CSS responderam HTTP 200.

## QA

- `anthares-studio/tests/qa_character_appearances_transaction.php`: **28 de 28 testes PASS** executados na instalação WordPress real, com ACF habilitado; `ROLLBACK=EXECUTED` e nenhum registro de homologação mantido.
- Casos: criação de três fichas de personagem, apelidos, homônimos, limites de palavra, registros Quill, distinção entre presença e menção, sugestões e contagem do gráfico, confirmação manual de pronome focalizador, recálculo após edição, reconciliação após inserção, invalidação de hash antigo, alerta de trecho modificado, remoção e bloqueio de outra conta.
- Contrato estático do item 11 e 25 verificações de integração do código aprovados.
- PHP 8.3 `-l` sem erros; JavaScript `node --check` dos dois scripts aprovado.
- Manifestos QA equivalentes com 748 arquivos auditáveis, sem arquivos ausentes ou duplicados.
- Publicação de capítulos G7 utiliza texto normalizado e escape de parágrafos; metadados privados das decisões não entram no conteúdo público.

## Homologação restante

O fluxo visual em navegador autenticado com um perfil real de aluno, incluindo marcação por seleção Quill com mouse/teclado, abertura da ficha e comportamento mobile, ainda deve ser realizado no **item 21**. O teste transacional em WordPress validou o comportamento de domínio e persistência, e a carga pública dos scripts foi confirmada. Não se afirma que essa inspeção visual já tenha ocorrido.

**Status de engenharia do item 11:** concluído em produção, sujeito à homologação visual geral do Studio.
