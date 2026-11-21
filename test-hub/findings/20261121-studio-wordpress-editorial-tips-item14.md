# Anthares Studio — Item 14: Dicas a partir de postagens nativas do WordPress

**Data:** 21/11/2026 (America/Campo_Grande)  
**Estado:** implementado e publicado no WordPress/Hostinger. QA transacional real e validação REST aprovadas.

## Requisito e fontes

Origem: `site-anthares.docx`, passagem “ah, tem uma coisa: eu preciso poder fazer postagens como em um blog comum...”, `PENDÊNCIAS URGENTES.md` item 14, `PLANO_MESTRE_IMPLEMENTACAO_ESTUDIO_ANTHARES.md` B27, `CONTRATO_NAVEGACAO_FIXA_ESTUDIO_ANTHARES.md` v2.

O autor do site publica **postagens comuns no WordPress**, atribuindo a categoria **Dicas de Escrita** (`dicas-de-escrita`). A partir dessa operação editorial usual, a postagem aparece no Studio sem importação, duplicação ou sincronização manual. O link do Studio é o permalink permanente do post original. O conteúdo permanece no WordPress e acompanha suas edições e alterações de status.

## Entrega

- **Seção Dicas:** dentro do projeto, em Planejamento → Dicas, na posição final da subnavegação interna. Rota SPA: `#studio/projeto/{id}/dicas`.
- **Navegação preservada:** cinco destinos globais, sete grupos internos, com Dicas apenas como ferramenta de Planejamento. A categoria de posts não cria um menu paralelo nem um CPT editorial adicional.
- **Busca e paginação:** listagem de artigos publicados, resumo, categorias, data e permalink. Busca textual com até 100 caracteres e limite de 12 registros por página; interface padrão com 9 itens e paginação.
- **Filtros:** Todas as dicas; Personagens; Enredo e estrutura; Pesquisa e referências; Ideias e planejamento; Manuscrito e cenas; Revisão literária; Publicação.
- **Dicas contextuais:** painel recolhível nas ferramentas de Pesquisa, Conceito/Planejamento, Personagens e universo, Estrutura, Manuscrito, Análises, Revisão e Publicação. Os posts são selecionados pelas categorias e etiquetas originais do WordPress. Painel contextual sem resultados apresenta estado vazio verdadeiro e link para a lista completa.
- **Curadoria editorial:** categoria-mãe obrigatória `dicas-de-escrita` (inclui descendentes). Para indicar assunto, o editor atribui adicionalmente uma categoria, como `personagens`, ou uma etiqueta contextual, como `dica-personagens`. Filtros usam condição E com a categoria-mãe e OU entre categorias/etiquetas do contexto. Nenhum artigo fora da categoria editorial aparece na listagem.
- **Proteções:** endpoint somente leitura, com login e direito de acesso ao Studio; consulta de `post_type=post`, `post_status=publish` e `has_password=false`; rascunhos, privados e posts protegidos por senha ficam fora. Links usam saída escapada, `noopener noreferrer`; respostas com `Cache-Control: private, no-store`.
- **Fórmula 1:** permanece como item 15, cuja especificação dos quatro campos é independente deste requisito.

## Repositório e versão

- PR de implementação: https://github.com/UniversoAnthares/anthares-wordpress/pull/401
- Merge: `2c0e61e230635848766a360c5f881dbe675aed87`

Cinco arquivos presentes na Hostinger, com hashes idênticos ao repositório:
- `anthares-studio/includes/domain/class-anst-editorial-tips.php`: `de7077f6b8b9545fdb9cac6b008ca2ae79f4f79c`
- `anthares-studio/assets/studio-editorial-tips.js`: `a91373df9c97145f42691c40a9c51374787020c3`
- `anthares-studio/assets/studio-editorial-tips.css`: `2b0b5d90e44f23c770aa3f2713868f1b1d87ca5d`
- `anthares-studio/assets/estudio.js`: `ac8ee2047bbd22ba5e2fbea010446eec29ba28a0`
- `anthares-studio/anthares-estudio.php`: `4a947f6a9f499217677f59e75a6255b68819db47`

Backups privados dos dois arquivos anteriores: `/home/u566597497/domains/anthares.us/studio-private-backups/20261121-item14-editorial-tips/` (fora de `public_html`). Todos os arquivos novos foram conferidos por SHA antes de transferência atômica, e os arquivos substituídos foram comparados com os hashes anteriores.

## Verificações

- **21/21 PASS** em `anthares-studio/tests/qa_editorial_tips_transaction.php`, executados antes e depois da implantação na própria instalação WordPress, com `ROLLBACK=EXECUTED`. Teste transacional criou temporariamente um post público, um rascunho e um post protegido, todos com as categorias editoriais; a consulta retornou somente o post público novo. Incluiu filtros de Personagens, Publicação, busca, página 2, permalink, exclusões e acesso anônimo negado.
- **6/6 PASS** em `anthares-studio/tests/test_editorial_tips_contract.py`, executados contra os arquivos de produção, cobrindo fonte WP, menu, tipagem de filtros, permissões, links e acessibilidade.
- **16/16 PASS** em verificações técnicas de integração do código.
- JavaScript `node --check`: PASS para `estudio.js` e `studio-editorial-tips.js`. PHP 8.3 `-l`: PASS para módulo e plugin.
- Manifestos QA duplicados sincronizados: 753 arquivos auditáveis, zero faltantes e zero duplicações; arquivos novos registrados em seus blocos.
- REST ativo: `/anthares-studio/v1/editorial/tips` registrado, chamada autenticada `HTTP 200`, **38 artigos publicados** retornados no total e 8 assuntos de filtro.
- URLs `/studio/`, `/estudio/`, JS e CSS da funcionalidade: todas `HTTP 200` após implantação. Os dados temporários de teste foram revertidos por transação.

## Limitação

O teste de navegação visual completa por um aluno em navegador conectado ao ChatGPT não ocorreu neste turno, pois a leitura das abas requer o navegador de origem com a extensão conectada. A execução real com diferentes contas, tamanhos de tela e cliques por toda a interface continua sob a homologação operacional do **item 21**. A API autenticada, os posts reais, os caminhos HTML/JS de navegação e a persistência editorial foram testados.

**Aceite de engenharia do item 14:** concluído em produção, com verificação visual ampla pendente no item 21.
