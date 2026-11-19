# G7 — universos, impacto, comentários e índice (QA real)

DATE_LOCAL: 2026-11-18, America/Campo_Grande
STATUS: PARTIAL
AREA: anthares-studio/G7
OWNER: ChatGPT (curso escrita criativa)
SOURCE_BRANCH: UniversoAnthares/anthares-wordpress:feat/studio-g7-beta-invites-20261118

## Testes de produção, com registros temporários excluídos

- Universos compartilhados: POST 200; idempotência com mesma chave e mesmo ID; reabertura GET 200; vínculo e desvínculo de segunda obra, ambos 200; conta não proprietária GET 404. Teste 21783.
- Fichas G7: registro vinculado por ID à enciclopédia, consulta e renomeação sem alteração de ID (21784, 21785); leitura externa 404; limpeza confirmada.
- ACF: personagem temporário (21787) vinculado a universo, biblioteca retorna source=acf e ID original; renomeação preservou referência; outra conta 404; limpeza confirmada.
- Impacto de alteração: capítulo de teste gravado com anst_meta_update ACF, marcação Quill aestEntity e ficha de continuidade. Consulta retorna 1 capítulo, 1 material e 1 marcação explícita. POST de comparação de campo ACF mudou somente a proposta, sem salvamento. Outra conta 404. IDs 21792–21794 excluídos.
- Comentários de versão: edição privada 21795 começou com política desativada, proprietário habilitou; outra conta recebeu 404; comentário de teste 3604 listado como pendente, aprovado e removido; leitura pública da edição privada permaneceu 404; fixture excluída.
- Índice público: edição privada 21796 retornou 404 para proprietário e visitante; removida.
- PHP lint: núcleo, universo, impacto, comentários e publicação PASS.
- Node --check: studio-g7-comments.js, universes.js, impact.js, public-reader.js, workspaces.js, publishing.js: PASS.
- Manifestos de QA: auditable=704, assigned=704, exactly_once=yes.

## Entregas

- Enciclopédia privada entre obras e referências ACF/G7 sem duplicação de IDs.
- Consulta de consequências de mudanças por vínculo Quill e registro G7.
- Comentários moderados por versão, parágrafo, resposta e spoiler, desligados inicialmente.
- Atualização da moderação na mesma aba.
- Controles de fonte e contraste no leitor.
- Índice de versões públicas autorizadas.

## Pendências / bloqueios

- O Chrome autenticado original não pôde ser controlado pela conexão disponível: leitura via Browser retornou falta de permissão da extensão; uma janela separada aberta pelo hub estava deslogada. Portanto, os testes de UI autenticada e dois usuários reais continuam pendentes.
- A edição pública, a Hotmart e as métricas seguem condicionadas a produtos e políticas oficiais; não habilitar recursos comerciais nem expor manuscritos de teste.
- Restam recursos G7 da matriz de 188 requisitos, incluindo revisão contextual aprofundada, continuidade em todas as vistas, colaboração/tutor, moderação, descoberta, sincronização de cenas e publicações e homologação móvel.
- Não declarar G7 totalmente concluído antes de aceite ponta a ponta. Não criar backups adicionais.

## Salvaguardas

Somente /studio/ foi alterado. /estudio/ não foi modificado nesta execução. Nenhuma edição pública foi ativada. Todos os posts e comentários temporários criados nesta rodada foram excluídos. Nenhum login ou credencial foi copiado.
