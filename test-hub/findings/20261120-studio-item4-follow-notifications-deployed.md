# Anthares Studio — Item 4: notificações internas de autores seguidos

**Data:** 20/11/2026. **Estado:** `ITEM4_DEPLOYED_VERIFIED`.

## Briefing e requisitos

- Briefing original: `site-anthares.docx`: botão para seguir autores e receber **notificações somente dentro do site, sem email**.
- Lista renumerada: **item 4 — Notificações de autores seguidos: avisos internos sobre novos capítulos e publicações**.
- Base: item 3, `_anst_g7_following_authors_v1`; sistema existente do Anthares `anthares_notificar` e preferências `Mensagens > Notificações`.
- Mantém excluído o item 13 original de remodelação da home. Não modifica a navegação fixa nem o arquivo `anthares-customify/author.php` divergente na produção.

## Código incorporado

- [PR WordPress #390](https://github.com/UniversoAnthares/anthares-wordpress/pull/390) merge SHA `e11fe54ffee7539f9ca7799210c846d5fc8fbc6b`.
- `anthares-studio/includes/domain/class-anst-g7-follow-notifications.php`: registra os tipos `studio_autor_novo_capitulo` e `studio_autor_nova_publicacao` no catálogo do sino, com a área `autores-seguidos`, event source e deduplicação por usuário/tipo/link e lock MySQL.
- `anthares-studio/includes/domain/class-anst-g7-publishing.php`: dispara `anst_g7_edition_published` somente após versão ser efetivamente pública; avisa ao retirar obras privadas e revogar publicação.
- `anthares-studio/anthares-estudio.php`: carrega módulo no plugin.
- Contos e posts seguem transição real para o estado `publish`; edição de publicação existente não dispara alerta novo. Eventos de rascunho ou conteúdo privado são ignorados.
- Preferências: novos tipos adicionados uma vez ao conjunto de tipos globais, se existente. Desativação administrativa e individual prevalece; quando desativado, não é inserido registro. Não usa e-mail.
- Ao remover publicação, os avisos são excluídos utilizando permalink registrado no envio; a implementação considera a mudança de permalink na retirada de publicação e serializa operações concorrentes.
- Fontes de perfil/seguidores não são copiadas; utiliza o `user_meta` privado do item 3.

## Testes

- PHP lint PASS no módulo e nos dois arquivos existentes alterados.
- **175/175 testes Python PASS** no checkout isolado.
- Manifesto QA **726/726 PASS**, cópias sincronizadas.
- **33/33 testes WP-CLI E2E PASS** em três contas pré-existentes e com publicações e notificações sintéticas em transação InnoDB. `ROLLBACK=EXECUTED`. Cobrem seguir e deixar de seguir; aviso de capítulo G7 autorizado; omissão de rascunhos; conto público; post público; bloqueio global/individual; idempotência; nenhum aviso para autor; limpeza de alertas após despublicação de capítulo/obra/post; HTTPS; restrição de acesso.
- Houve uma falha de teste sobre mudança de permalink quando o post passava a privado, corrigida no PR antes de implantação e retestada; segunda bateria transacional 33/33 aprovada.
- Em produção: **51/51 testes do plugin PASS**, plugin ativo.
- Após implantação, `studio_autor_novo_capitulo` e `studio_autor_nova_publicacao`: `REGISTERED` e `ACTIVE=YES`; área `autores-seguidos=OK`. `anst_g7_follow_notice_types_registered_v1=1`.
- /studio/ e /estudio/ HTTP 200; rota anônima GET /g7/following HTTP 401; **22 projetos originais da conta de homologação** preservados.

## Instalação na Hostinger

Caminho: `/home/u566597497/domains/anthares.us/public_html/wp-content/plugins/anthares-studio/`.
Arquivos instalados, hashes SHA-256 conferidos contra o checkout do merge:

| Caminho relativo | SHA-256 |
|---|---|
| `includes/domain/class-anst-g7-follow-notifications.php` | `ee7d943d066c190b4c314783fe02f98c70365b448c0f2a34deecf56fbf30b854` |
| `anthares-estudio.php` | `e82b17b941f1a5b7d23ef2f156781e80e741eef60dd3fc409177cdbdf68a92aa` |
| `includes/domain/class-anst-g7-publishing.php` | `82a4439b735090cb272551fb89295b037a9b64d41e3a992906ff378ae20f6c9e` |

Backup privado dos dois arquivos originais: `/home/u566597497/.anthares-studio-private-backups/item4-follow-before-20261120.xchnKl`. Usado `flock` exclusivo, comparados hashes do `main` anterior à escrita; deploy `DEPLOY_SUCCESS`. Nenhuma alteração em tema, outros sistemas, compras, ou conteúdo real.

## Continuidade

- Itens **1–4 concluídos e implantados**. **18 itens restantes** da lista de 22.
- Próximo: item 5, descoberta pública por gênero, assunto e etiquetas.
- Para confirmar avisos visíveis a leitores reais, usar publicação futura autorizada de autor seguido e inspecionar o sino. Os testes funcionais e transacionais foram aprovados e revertidos sem gerar avisos efetivos para contas reais.
