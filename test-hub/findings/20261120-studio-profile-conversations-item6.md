# Anthares Studio — Pendência urgente 6: conversas e comentários nos perfis

Data: 20/11/2026. Estado: **CONFIRMADO EM PRODUÇÃO**, com testes transacionais e inspeção HTTP.

## Entrega implementada
- Seção **Conversas** incorporada a cada perfil público em `/author/{autor}/`, ligada à navegação existente, preservando o tema ativo da Hostinger.
- Mensagens e respostas encadeadas (profundidade controlada), contextualizadas por perfil.
- Comentários de visitantes aguardam moderação do autor; moderação autorizada somente ao proprietário/administrador.
- Configuração de pausa de comentários; validação de CSRF com nonce; limite de 2.200 caracteres; intervalo mínimo de 30 segundos; proteção contra resposta a comentário não aprovado ou de outro perfil.
- Notificações internas para moderação pendente e respostas, por meio do serviço `anthares_notificar()`.
- Dados separados das edições/capítulos, por CPT técnico privado `anst_g7_profile_wall` e `wp_comments`.

## GitHub
- Repositório: `UniversoAnthares/anthares-wordpress`
- PR implementada/mergeada: https://github.com/UniversoAnthares/anthares-wordpress/pull/392
- Merge commit: `d688bded6e81fa3f3c9fac330feda172327db6a6`
- Plugin `anthares-studio/anthares-estudio.php`: blob SHA `b8079f7971bd64a1257208ce70f1c5c46af5d4f1`
- Novo `anthares-studio/includes/domain/class-anst-g7-profile-conversations.php`: blob SHA `0badfa452e73c2a0c616c5afde22fe118cee80c3`
- QA: `anthares-studio/tests/test_g7_profile_conversations_contract.py`; manifestos de cobertura atualizados em sincronia.

## Produção na Hostinger
- Os dois arquivos instalados foram conferidos por `git hash-object` e coincidem com a branch principal.
- `php -l` do plugin e do módulo: PASS (PHP 8.3).
- `/studio/` HTTP 200; `/estudio/` HTTP 200; tema ativo `anthares-customify/author.php` preservado com SHA `7edba6281348a6cfa62807e19c3b1c31d679f87b`.
- Perfil público ativo contém marcador `anst-g7-profile-mount-script`; seção inserida após `perfil-avaliacoes`.
- Antigo arquivo `anthares-estudio.php` guardado em backup privado fora de `public_html`, SHA `f8c81ec5e27f2412907f4fbe62ce814114554eae`.

## Evidências de QA
- 15 verificações estáticas dos contratos de autorização, moderação, isolamento, integração e manifestos: PASS.
- **14/14 verificações transacionais** em WordPress com proprietário e dois usuários leitores, cobrindo criação, ocultação de pendências, permissões, aprovação, resposta e vínculo de conversa: PASS.
- **2/2 verificações transacionais** do sistema de notificações, área autorizada e registro interno: PASS.
- Ambos os testes executados em `START TRANSACTION` com `ROLLBACK` e `pre_wp_mail` bloqueado, preservando dados reais.
- Consulta posterior: **zero** posts residuais do CPT `anst_g7_profile_wall` e **zero** scripts temporários próprios em `/tmp`.

## Limite do teste
Foi comprovada a execução PHP/WordPress real com três contextos distintos de usuário e o HTML entregue publicamente. Uma sessão manual de browser simultânea com duas contas distintas permaneceu fora do escopo. A operação foi concluída sem alterar o plugin legado nem o tema ativo.

## Resultado
Item 6: **CONCLUÍDO**, por evidência de código implantado, execução no site, persistência dentro de transação, moderação e reversão integral da massa de testes.
