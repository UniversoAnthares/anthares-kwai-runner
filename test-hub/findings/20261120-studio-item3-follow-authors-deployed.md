# Anthares Studio — Item 3: seguir autores (implantado e homologado)

**Data:** 20/11/2026, revisão após implantação 19:41 UTC. **Estado:** `ITEM_3_DEPLOYED_VERIFIED`.

## Fonte e escopo autorizado

- Briefing original `site-anthares.docx`: *“cada usuário tem que ter um botão de seguir, pra quando esses autores publicarem aparecer na home de quem quer acompanhar”*.
- Lista de pendências ativa renumerada: **item 3, Seguir autores: acompanhar escritores e suas publicações**.
- Implementado botão **Seguir autor/Deixar de seguir** em perfis públicos e leitura pública, além de **/studio/?autores_seguidos=1**, com lista pessoal e publicações recentes de autores acompanhados.
- **Item 4, Notificações de autores seguidos**, continua pendente e independente; não foi enviado e-mail, notificação ou publicação.
- Item 13 original (seções editoriais da home) excluído do escopo por decisão do titular; o feed desta entrega é na página pessoal de autores acompanhados, sem modificar a home pública.

## Código e PRs

- [WordPress PR 387](https://github.com/UniversoAnthares/anthares-wordpress/pull/387): módulo PHP de autor seguido e REST autenticado, widget JS/CSS, shortcode pessoal, leitor público, perfil, links de navegação.
- [WordPress PR 388](https://github.com/UniversoAnthares/anthares-wordpress/pull/388): adapta perfil para hook `wp_footer`, preservando alterações do tema ativo `anthares-customify/author.php` existentes na Hostinger. O arquivo do tema **NÃO foi sobrescrito**.
- [WordPress PR 389](https://github.com/UniversoAnthares/anthares-wordpress/pull/389): normalização dos links HTTP que o WordPress emite atrás do proxy TLS; a UI promove URLs do próprio `anthares.us` para HTTPS e descarta protocolos/hosts inseguros. Main merge commit `2ec13f4c270810eec60bf09cb32d1bfd370a4317`.

## Superfície instalada (plugin apenas, 7 arquivos)

Diretório: `/home/u566597497/domains/anthares.us/public_html/wp-content/plugins/anthares-studio/`.

| Arquivo | SHA-256 conferido (igual à main do GitHub) |
|---|---|
| `includes/domain/class-anst-g7-following.php` | `2e29d2abaf94174ae6b71aa2bf25ffa5ae2b02c81284e8834e0ad14bbd916557` |
| `assets/studio-g7-follow.js` | `037fd275afb38e9388b21e7f985c5c3930996b93e2a50bea829865ff4eeb9718` |
| `assets/studio-g7-follow.css` | `d137e01b0b469e05960f62cd7255db06dcde00d9f61081415189c457148a296f` |
| `assets/studio-g7-library.js` | `283cd9c4d0d01ffc6ccc3f8c2dbe61621cac7843e5e5e00953b3503d18f0f2b4` |
| `assets/estudio.js` | `c738eb60942e905eaf9e27b8be656ce0a7dbc2f64c966ba85383394d4fced1f0` |
| `includes/domain/class-anst-g7-publishing.php` | `b3d1962ba660200f0faef073a6ec963adb7f65dd06e0111cc00af8885adb9e8f` |
| `anthares-estudio.php` | `5ce58b1ccf0d9ef6ce0479cadd36a271be5a683a51f82b8ac1f542d3a14ddd63` |

O arquivo do tema ativo `wp-content/themes/anthares-customify/author.php` foi preservado, SHA-256 `56eaf84892927e70c7782dc663b79f942fe7de8ef5a5b2c51153fac217131e9e`; seu conteúdo difere significativamente do snapshot do repositório. **Não publicar a versão do GitHub sobre esse arquivo sem reconciliar esse drift.**

Backups privados fora do `public_html`: `/home/u566597497/.anthares-studio-private-backups/item3-follow-before-20261120.jNWNNp` e `/home/u566597497/.anthares-studio-private-backups/item3-follow-js-before-https-20261120`. O executor da implantação retornou HTTP 500 após possivelmente aplicar a atualização; a instalação foi **reconciliada por SHA dos sete arquivos** antes de qualquer nova escrita. Não houve repetição indevida.

## Homologação

- Código branch: **161/161 testes Python PASS**; manifesto duplo de QA **723/723 PASS**; sintaxe PHP e JS aprovadas.
- WP REST E2E: **31/31 verificações PASS** em três contas existentes, usando publicações e metadados sintéticos dentro de transação InnoDB e `ROLLBACK=EXECUTED`. Testadas autenticação, persistência, seguir/desseguir idempotente, conta própria, identidade de outros usuários, filtro de publicações privadas, revogação, acesso a dados e consulta resumida.
- Navegador isolado (abas criadas e fechadas): botão Seguir/Deixar de seguir e filtro de publicações aprovados; CSS sem overflow horizontal em 390/768/1440 px. A URL HTTP do próprio WordPress é promovida a HTTPS; URL maliciosa `javascript:` ignorada.
- Pós-instalação: **7/7 hashes iguais ao código canônico**; JavaScript servido por HTTPS com hash exato; `/studio/` e `/estudio/` HTTP 200; endpoint público `/wp-json/anthares-studio/v1/g7/following` sem login HTTP 401; REST autenticado no WP-CLI HTTP 200; plugin ativo e PHP lint PASS; 51/51 testes do plugin em produção PASS.
- **Perfil público real** `/author/lucasyahn/`: HTTP 200, widget e JS entregues pelo servidor; teste Chrome mostrou `movedIntoProfile=true`, `profileTitle=true` e `loginLink=true` para visitante anônimo. Não foi editado nenhum dado existente. **22 projetos originais preservados**.

## API e privacidade

`GET/POST /wp-json/anthares-studio/v1/g7/following`, protegidos pelo nonce REST e autenticação. O mapa privado de IDs de autores está em `_anst_g7_following_authors_v1` do usuário; limite 200 autores, lock por conta. Seguir é idempotente, próprio usuário é bloqueado, dados de outros leitores não são retornados. Feed restrito a contos/posts públicos e edições de capítulo G7 validadas por `anst_g7_edition_published`; referências a publicações revogadas desaparecem imediatamente do feed. Nenhuma mensagem é enviada nesta entrega.

## Continuidade

- Item 3: **concluído, implantado, comprovado**.
- Itens 1 e 2: concluídos antes, com evidências em `20261120-studio-item1-hostinger-deployed.md` e `20261120-studio-item2-library-deployed.md`.
- Item 4: notificações internas de autores seguidos **pendente**, deve usar o sistema Anthares existente e preferências do usuário; e-mail explicitamente não solicitado no briefing.
- Revisão do tema `author.php` entre GitHub e Hostinger precisa de fluxo de reconciliação independente antes de futuros deployments que incluam o tema. Não impede a função seguir autores já implantada.
