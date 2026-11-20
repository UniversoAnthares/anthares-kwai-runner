# Anthares Studio — homologação funcional parcial (20/11/2026 UTC)

## Ambiente
- Produção: `https://anthares.us/studio/`; plugin `anthares-studio` ativo, versão `0.7.8-staging`.
- Legado `/estudio/`: preservado; nenhum arquivo ou conteúdo alterado.
- GitHub main de referência: `075e525780064340f28eceb59b128ef4de5f13c8`.
- Leases: somente verificação de fluxos, sem deploy ou criação de contas.

## Testes comprovados
- Python unittest instalado: 51/51 PASS (verificação anterior na mesma instalação).
- Sintaxe PHP: `anthares-estudio.php` e 20 arquivos em `includes/` sem erro.
- JavaScript servido na produção: 14/14 arquivos compilados por `node:vm.Script`, sem erro de sintaxe.
- REST WordPress interno: 54 verificações de sucesso (linhas PASS) para administrador autorizado:
  bootstrap completo e por projeto; criar/renomear/colorir/arquivar/reativar projeto; criar/editar nota; conflito de revisão 409; criar/editar/duplicar cartões; criar/salvar/reordenar capítulos; rejeitar salvamento sem precondição 428 e hash desatualizado 409; listar/criar snapshots; posição estrutural; status e autorização comercial da publicação G7; lixeira, restauração e cascata; bloqueios anônimos.
- Segurança: GET `/bootstrap` e POST `/projects` anonimamente devolveram 401; tentativa de publicar sem direito validado 403. Conteúdo da fixture retido apenas dentro de transação InnoDB; ROLLBACK confirmado, contagem de posts inalterada e 0 posts de teste persistidos.
- Browserless em 390px: HTML `/studio/` 200, tela de acesso presente, sem transbordamento horizontal.
- Chrome AntharesWordPressAdmin existente: a página mantém `aest-access-gate`; medição a 792px sem transbordamento; quatro folhas de estilo do Estúdio carregadas. Perfil não apresenta sessão autenticada utilizável para navegação interna.

## Limitações observadas
- Homologação de cliques reais nas sete abas internas, editor Quill, upload, responsividade de telas autenticadas e persistência pelo navegador permanece PENDENTE DE LOGIN. Os testes REST autenticados por WP-CLI não substituem o percurso visual de um cliente real.
- Browserless desktop chegou a página de desafio HTTP 403 em uma tentativa; resultado não comprova defeito do site.
- A criação de usuário temporário de QA foi bloqueada pela configuração de segurança da ferramenta; não houve contorno, usuário de teste ou credenciais persistidas.
- Uma tentativa adicional de simulação de propriedade entre dois administradores também foi bloqueada; não foi executada.

## Encerramento
Nenhuma alteração em dados reais, plugins ou permissões. O script privado de QA foi removido; nenhum arquivo de credencial temporário criado. Usuário precisa realizar login no perfil de navegador apropriado e solicitar continuação dos testes visuais; não declarar homologação E2E completa até essa etapa.
