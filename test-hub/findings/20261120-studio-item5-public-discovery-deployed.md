# Anthares Studio — Item 5: descoberta pública de obras

**Data de instalação:** 20/11/2026. **Estado:** `ITEM_5_DEPLOYED_VERIFIED`.  
**Fontes:** `site-anthares.docx`, parágrafos 3–8; `ANTHARES_STUDIO_PENDENCIAS_ATIVAS_RENUMERADAS_2026-11-20.md`, item 5, “Descoberta pública por gênero, assunto e etiquetas”.

## Requisito implementado

- Busca pública em `https://anthares.us/studio/?descobrir_obras=1`, disponível a visitantes anônimos e contas sem direito de acesso ao curso.
- Filtros por palavra (título e sinopse pública), gênero literário, assunto e etiqueta, combináveis. Resultados em páginas de 12 obras, com links para a obra e perfil do autor, além de chips clicáveis de etiquetas.
- Campos públicos **Assunto** e **Etiquetas** na interface de publicação autorizada do Studio, junto a título, sinopse, gênero e estágio. Até 12 etiquetas de 32 caracteres, deduplicadas pelo slug. O autor confirma a exposição pública.
- Consulta REST `GET /wp-json/anthares-studio/v1/g7/discovery` e página HTML renderizada no servidor, ambas somente com dados explicitamente públicos.
- A consulta SQL usa parâmetros preparados, exige `anthares_projeto` publicado/sem senha, `_anth_projeto_mostrar_perfil=1`, vínculo bidirecional ao `anst_projeto` e visibilidade `publico_em_desenvolvimento` ou `obra_publicada`. Revogações removem resultados imediatamente. Conteúdos privados de capítulos, pesquisa e fichas são excluídos.
- Atalho **Descobrir obras** na página inicial do Studio; cinco itens globais da navegação preservados. Sem integração com segmentação demográfica do item D descartado pelo usuário.

## Código

- PR [UniversoAnthares/anthares-wordpress#391](https://github.com/UniversoAnthares/anthares-wordpress/pull/391), **merged**, commit principal `bfc124debdf1b48166413c0689a4ac35c393dacb`.
- Caminho ativo: `/home/u566597497/domains/anthares.us/public_html/wp-content/plugins/anthares-studio/`.
- Arquivos implantados e SHA-256 verificados contra `main`:
  - `includes/domain/class-anst-g7-discovery.php`: `60bf6eb1fa79950b943059d4a4fce5deef4c0badbb6ca4fcd92b046aaae07936`
  - `anthares-estudio.php`: `aa71c299941462709b4261c75e748936e9b6839c7b746e4144a23b83b12edf6a`
  - `includes/domain/class-anst-g7-publishing.php`: `c1acd3e689a0536da6c4252c33ca1b9fa743356e102f496cca7b49e03c056adc`
  - `assets/studio-g7-publishing.js`: `859179ee7226679d7ba864dd2583a7cfebd257f2e6cfb2908b6f9a142696d9e1`
  - `assets/estudio.js`: `cb550d5faed18ccc4552a8502b9e03c533864d796f1cf50c4209529f0d72fc48`
  - `assets/studio-g6-navigation.css`: `ac0840ed9ca916eccbb5c45d03d8e184987e2d25d717012fa94e6dcbb3f7c9b8`
- Backup privado dos cinco arquivos substituídos: `/home/u566597497/.anthares-studio-private-backups/item5-discovery-before-20261120.Ch5T1T`.
- Preflight comparou hashes de cinco arquivos ativos contra o primeiro pai do merge PR #391; todos iguais, sexto arquivo novo ausente. Instalação via integração autorizada SSH Hostinger com lock exclusivo, backup privado, rollback automático em erros, e saída `DEPLOY_SUCCESS`. Tema `anthares-customify/author.php` preservado, devido a divergência já documentada.

## Testes e evidências

- **191/191 testes Python** PASS no checkout isolado, abrangendo o módulo e a pilha anterior. Verificação PHP lint PASS; `node --check` para `studio-g7-publishing.js` e `estudio.js` PASS.
- **37/37 cenários de integração WP-CLI/REST PASS**, usando obras públicas, privadas, não listadas, retiradas e despublicadas, incluindo criação de metadados pelo endpoint de publicação autorizada, validação e deduplicação de etiquetas, filtros compostos, normalização de acentos, paginação 12+2, tratamento de parâmetros malformados e tentativa de injeção SQL. Final com `ROLLBACK=EXECUTED` em tabelas InnoDB; nenhum dado de usuário ou conteúdo público permanente foi criado.
- Manifesto QA duplicado: **729/729 PASS**, todos os arquivos classificados exatamente uma vez.
- **51/51 testes do plugin em produção PASS**; plugin ativo; hashes 6/6 correspondem ao commit do PR.
- HTTP `/studio/` 200, `/estudio/` 200; página de descoberta anônima renderizou `#aest-g7-discovery` e campos `q`, `genre`, `subject`, `tag`; API anônima `/g7/discovery` HTTP 200; **22 projetos originais** preservados.
- Browser Chrome, somente aba QA criada e encerrada, sem interferir na aba pessoal: formulário e estilos válidos nas larguras **390, 768 e 1440px**, sem overflow horizontal; `aest-access-gate=false`.
- A consulta real apresentou **0 cards públicos no instante do teste**, pois ainda não havia obras públicas G7 elegíveis na pesquisa geral. A homologação de cards e filtros usou fixtures reversíveis. Isso não implica falha da funcionalidade nem comprova fluxo visual sobre obra real publicada.

## Continuidade

- **Itens 1–5 concluídos tecnicamente e implantados. Restam 17 itens**.
- Próximo: **item 6 — Comentários nos perfis**.
- O item 21 permanece como homologação mais abrangente de contas, dispositivos, projetos extensos e publicação pública real.
- Sem mudança em pagamentos, direitos comerciais, seleção demográfica de resultados, autorizações comerciais nem no sistema antigo `/estudio/`.
