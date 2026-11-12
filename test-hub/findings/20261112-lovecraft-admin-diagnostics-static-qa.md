# Lovecraft — leitura de falhas agregadas e QA estático da recuperação
STATUS: PARTIAL
AREA: wordpress/lovecraft-publication-recovery
DATE_UTC: 2026-11-12
OWNER: chatgpt-gpt6-lovecraft-partial-20261112
LEASE: CLOSED
SUPERSEDES: test-hub/findings/20261112-lovecraft-partial-repair-source-staged.md
SOURCE_PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/268
WORDPRESS_BRANCH: fix/lovecraft-retry-partial-translation-and-accurate-warning-20261112

## Novas provas nesta revisão
1. A branch de origem possui alterados quatro arquivos preexistentes, todos presentes exatamente uma vez em cada manifesto idêntico de QA (ambos blob SHA caac5ee7b6c20f4e8713dfb67ca4a77be52f129f). Não há novo arquivo auditável no WordPress.
2. Em executor externo preexistente e autorizado "Anthares QA Executor Reserva" foi carregado um parser PHP 3.2.5 com gramática 8.2; quatro fontes completas do commit foram convertidas em AST com suppressErrors=false e zero exceções: includes/18 SHA eb423eaa90aa9eaa465d0539931197ea5e06a580; includes/19 SHA 6fa26a3845a2d5db337c6804ebda17656ffbb35f; includes/21 SHA 62102e6b7f111d06b398ed997ba39c51d8bbf5bf; tests/lovecraft-recovery-contract.php SHA e4eb7d670600fb8e175bbdfd9a1a71e43b593015. Verificação sintática AST concluída; **isso não substitui php -l nem execução das asserções PHP**.
3. O painel de administração agora calcula o número de traduções parciais, quarentenas ativas, categorias de falha (metadados, capa, título, taxonomia, validação e outras) e próximo retry, sem exibir erros brutos/cookies/tokens. Usa apenas get_option e SELECT agregado e preserva status e posts.
4. O teste offline existente foi corrigido para usar o caminho real de includes e os stubs de hooks WP comuns, sem criar testes novos.
5. O perfil dedicado AntharesWordPressAdmin existe, porém leitura autenticada redireciona para /wp-login.php (senha requerida), em 2026-11-12; não há leitura autorizada do option privado anthares_lc_falhas_publicacao. As capturas do titular mostram contagens 108 traduzidos, 338 publicados, 6 pendentes e 2 erros, mas não quantificam falhas por categoria.
6. O TinyFish wallet foi verificado: quota/recursos insuficientes para operações de navegador pagas; regra sem custos novos preservada. Nenhuma automação paga foi iniciada.

## Critério terminal pendente
Rodar php -l e suites funcionais de PHP em executor não pessoal com quota disponível, obter diagnóstico administrativo autenticado, confirmar que o reparo corresponde à causa real, revisar mudanças concorrentes e implantar apenas com owner/rollback; então colher recibo de publicação real segura. PR permanece draft, sem merge ou alteração no site real. O cron no site segue a configuração existente. Não iniciar publicações de teste nem repetir falhas por outra ferramenta após recusa expressa.
