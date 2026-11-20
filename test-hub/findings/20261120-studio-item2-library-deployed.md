# Anthares Studio — Item 2: biblioteca de leitura concluída
Data: 2026-11-20, produção confirmada após merge.

## Requisito e referência
- Origem: `site-anthares.docx`, trecho “qualquer usuário pode marcar pra acompanhar ou favoritar textos...”
- Lista ativa renumerada: item 2, “Favoritos e listas de leitura: salvar, organizar e acompanhar obras”.
- Próxima revisão do projeto: marcar item 1 e item 2 como implementados e implantados; itens 3–22 seguem pendentes conforme documento das Fontes.

## Implementação no código
- PR [anthares-wordpress#386](https://github.com/UniversoAnthares/anthares-wordpress/pull/386) MERGED no commit `9ca9920ba79ed0276e5a89e2513461abb088daa5`.
- `includes/domain/class-anst-g7-library.php`: `GET/POST /wp-json/anthares-studio/v1/g7/library`, com autenticação, dados por usuário em `user_meta`, limite de 250 obras e 20 listas, lock MySQL por usuário, validação da publicação autoritativa, remoção e edição de listas, favorito e retomada de capítulo.
- `assets/studio-g7-library.js`: controles no leitor público; interface pessoal `/studio/?minhas_leituras=1`; listas personalizadas, filtro, adição/remoção e favorito; registro do capítulo visitado apenas quando obra já estiver salva.
- `anthares-estudio.php`: shortcode próprio sem exigir compra do curso, mas exigindo usuário autenticado, script enfileirado com nonce WP.
- `assets/estudio.js`: atalho “Minhas leituras salvas e favoritos” na página inicial sem alterar os cinco itens globais.
- `assets/studio-g6-navigation.css`: interface responsiva, foco por teclado e organização dos controles.
- `tests/qa_g7_library_transaction.php`, `tests/test_g7_library_contract.py`: testes novos.

## Testes comprovados
- **30/30 REST E2E PASS** usando dois leitores existentes e um autor administrador, posts e user_meta sintéticos em transação InnoDB, `ROLLBACK=EXECUTED`. Testados: sessão persistente/limpeza de cache, isolamento A/B, salvar/remover, favorito idempotente, listas criar/renomear/atribuir/excluir, última edição, fallback de edição revogada, privacidade de projeto privado, negacões de acesso anônimo.
- **144/144 Python unit tests PASS** na branch; QA manifest preflight **718/718 PASS**, duas cópias sincronizadas; lint PHP PASS, sintaxe JS PASS.
- Chrome CDP em aba isolada, fechada: interface de leitor salva e favorita; página de biblioteca exibe obra, cria lista e atribui livro; larguras 390/768/1440 sem overflow horizontal detectado.
- Pós-produção: `/studio/` e `/estudio/` HTTP200; página `/studio/?minhas_leituras=1` oferece login seguro para visitante; nenhum conteúdo privado exposto; `GET /g7/library` anônimo HTTP401; shortcode autenticado e rota REST registrados; JS e CSS servidos por HTTPS com hashes idênticos aos locais; 51/51 testes existentes do plugin PASS.
- Navegador WordPress disponível neste momento sem sessão autenticada; por isso, o teste de interface autenticada real foi executado em Chrome isolado com API simulada e a persistência verdadeira foi verificada via integração REST em duas contas existentes. Não confundir com homologação multi-dispositivo em produção do item 21.

## SHA-256 em produção
- `anthares-estudio.php`: `14bc32983f4f63d250e2e48a9ab9c0ab88c5398d71768745ae3d775c0449a674`
- `assets/estudio.js`: `1139754375379aed77c071d98d32351f0d754d7289cff01731e20fec0209afaf`
- `assets/studio-g6-navigation.css`: `d9a5e707131802a62ef840772fdeb2855d926dd09548575a24a83c57e0827f97`
- `assets/studio-g7-library.js`: `9df4c355252e1649de7bd212a1d4e1184359c55191425704010a5a18acb2c090`
- `includes/domain/class-anst-g7-library.php`: `1699161257ba91e2fbb3f7ff54be5801fa3146a49921ceaf6292d28eac3478fc`

## Operações e segurança
- Instalação realizada por integração remota autorizada, SSH existente Hostinger.
- Antes de escrever: três arquivos existentes foram comparados por SHA com o `main` anterior ao PR, e os dois arquivos novos estavam ausentes; sem conflito de produção.
- Backup dos três originais fora do diretório público: `/home/u566597497/.anthares-studio-private-backups/item2-library-before-20261120.bnTDQE`.
- Os cinco arquivos instalados coincidem com o merge main, checados separadamente depois de resposta 500 do executor; estado reconciliado e confirmado.
- Projetos anteriores: **22** publicados para a conta de homologação, contagem preservada. Sem publicações novas, pagamentos, envio de mensagens, criação de contas ou dados reais alterados.
- O recurso é exclusivo das obras publicadas pelo novo Studio (G7). Integração futura com outros formatos de contos do Anthares pode ser avaliada no item 5, preservando as relações existentes.

ESTADO: **ITEM_2_DEPLOYED_AND_VERIFIED**.
