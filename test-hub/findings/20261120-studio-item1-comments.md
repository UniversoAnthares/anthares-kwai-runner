# Anthares Studio — Pendência ativa 1: comentários por parágrafo
Atualização: 2026-11-20
Referências: `site-anthares.docx`, parágrafo "o site é uma plataforma de postagens de histórias..."; `ANTHARES_STUDIO_PENDENCIAS_ATIVAS_RENUMERADAS_2026-11-20.md`, item 1; Plano Mestre B24.

## Código
- PR https://github.com/UniversoAnthares/anthares-wordpress/pull/385 incorporado à `main`; merge commit `34f73c11b0cddf45fb8428bc078b1b60332e4279`.
- `anthares-studio/assets/studio-g7-comments.js`: marcadores por parágrafo, painel lateral, discussão contextual, respostas encadeadas, spoilers, navegação por links diretos e moderador com listas pendente/aprovada.
- `anthares-studio/assets/studio-g6-navigation.css`: duas colunas no desktop, painel após o texto no celular, navegação por teclado, sem overflow nas larguras verificadas.
- `anthares-studio/includes/domain/class-anst-g7-comments.php`: valida só parágrafos visíveis, respostas herdam a âncora do comentário pai e permanecem na mesma edição, moderação por proprietário, três notificações internas pelo `anthares_notificar` respeitando preferências.
- Testes: `anthares-studio/tests/test_g7_comments_context.py` e `anthares-studio/tests/qa_g7_comments_transaction.php`.

## Evidências
- Sintaxe PHP: PASS. JS `node --check`: PASS.
- Python: **130/130 PASS** no checkout isolado.
- Integração WordPress (três contas reais preexistentes, com posts e comentários sintéticos dentro de transação InnoDB): **22/22 PASS** e `ROLLBACK=EXECUTED`. Confirmado que comentários da edição antiga não migram para nova, parágrafo vazio rejeitado, resposta pendente rejeitada, autônomo não autorizado, moderação e notificações.
- Teste de UI em Chrome headless com dados simulados: marcadores=2, comentários=2, seletor de resposta preserva parent=301 e paragraph=3; layout responsive em 390, 768, 1440 px sem overflow.
- Manifesto QA duplo: **714/714 PASS**, bloco B com os dois novos arquivos de teste.
- Nenhum conteúdo real ou cadastro foi editado; transação revertida.

## Estado de instalação
- No instante de 20/11/2026 15:34 UTC, as três versões de código **ainda eram antigas na Hostinger** (hashes divergentes do PR).
- ZIP verificado: `https://anthares.us/wp-content/uploads/anthares-studio-item1-comentarios-20261120.zip` (HTTP 200; SHA256 `7796efad7e9e3590bb2c2d977de1bc3b6bdc548ebb401e5fbe1ae476adc20fbc`).
- Estrutura: `anthares-studio/assets/studio-g7-comments.js`, `anthares-studio/assets/studio-g6-navigation.css`, `anthares-studio/includes/domain/class-anst-g7-comments.php`.
- O usuário instalou anteriormente patches semelhantes manualmente por FTP. A instalação ativa e a verificação E2E pós-FTP permanecem pendentes; **não marcar item 1 como concluído em produção antes dessa conferência**.
- O código de produção e os dados de `/estudio/` foram preservados durante esta implementação. O item 6 (comentários em perfis) segue independente.
