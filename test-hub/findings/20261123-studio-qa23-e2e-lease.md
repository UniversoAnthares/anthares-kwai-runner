# Test Hub — lease QA23 E2E, perfis, carga e recuperação (2026-11-23)
STATUS: RUNNING
AREA: studio
DATE: 2026-11-23
OWNER: ChatGPT / QA_STUDIO_23_E2E_20261123
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/422
JOB: local Playwright isolated browser + wp-cli PHP 8.3
COMMIT: 5ff987ba849f576cbc898b1bce8e6bb52737ff0e
SUPERSEDES: none

## Objetivo
Completar os cenários restantes do item 23 sem comprometer usuários reais, site legado /estudio, credenciais nem publicações.

## Baseline comprovada
test-hub/findings/20261123-studio-qa23-results.md: 68/68 SHA; 183/183 testes transacionais PASS + ROLLBACK; 6 papéis; 268 contratos. Projeto WordPress main 5ff987ba.

## Escopo
1. Criar contas temporárias sintéticas com prefixo exclusivo qa23_<identificador>, e-mails .invalid e notificações WP interceptadas; comprador com direito ativo, comprador expirado, autor e leitor, com sessões efêmeras em navegador isolado Playwright.
2. Criar projetos e notas de QA somente nas contas de teste, e remover todo o conteúdo/cookies/sessões temporários após testes. Registrar antes/depois contagem por tipo e limpeza; não excluir registros fora do prefixo sintético.
3. Checar navegador desktop/mobile, teclado, erros REST 401/403/409, exclusão de sessão e persistência; testar concorrência em duas sessões e carga limitada em projeto sintético. Restaurar versões em projeto sintético.
4. Toda experiência com pagamentos, Hotmart, WooCommerce real, emails, notificações externas, serviços terceiros, publicações públicas e dados de usuários reais permanece desabilitada. Checkout real e ações irreversíveis estão excluídos.
5. Corrigir código apenas em branch, com testes, PR e deployment verificado quando seguro.

## Segurança
Evitar logs de cookies, senhas, endereços de e-mail, identificadores pessoais e textos privados. Usuários/fixtures temporários apenas para QA. Nenhuma credencial fornecida a terceiros; scripts locais controlam sessões em memória. Abortar ações que aparentem envolver dados de contas reais.
FAILED_AVOIDED: CLI PHP 7.4 inválido; usar PHP 8.3. Browser sem CDP existente; usar Playwright headless isolado. Nenhum Test Hub finding editado; append-only.
SUCCESS_SIGNAL: cenários rastreados por ambiente, SHA, método, observação e prova; limpeza verificada e ausência de efeitos fora do QA. Qualquer lacuna permanece PARTIAL.
