# Papel anthares — oferta de contos beta plenamente habilitada em produção
STATUS: PROVEN
AREA: wordpress-home-beta-role
DATE: 2026-10-31
RUN: Hostinger SSH / WP-CLI validação sem escrita
JOB: chatgpt-20261031-beta-role-promotion
COMMIT: b1d627cced8fccab6cfca92448bc8949add75723
SUPERSEDES: test-hub/findings/20261031-lease-anthares-beta-role-promotion-gpt6.md

## Objetivo e resultado
A função `anthares_beta_host_pode_disponibilizar_contos()` aceita o papel exato `anthares` independentemente da Etapa 3, preservando a regra anterior de Etapa 3 para os demais papéis. O fluxo `anthares_beta_processar_conto_pendente()` autoriza salvar um conto em beta para o papel `anthares`; validações de nonce, autoria, limite, reserva e transferência de Runas permanecem.

## Evidência decisiva
- Código: `UniversoAnthares/anthares-wordpress` PR #210, merge squash `b1d627cced8fccab6cfca92448bc8949add75723`.
- Testes externos: PHP 8.3 lint PASS; `qa/manifest-coverage-preflight.py --check`: PASS 599/599, exactly_once=yes; `qa/anthares-orchestrator-qa.php`: PASS.
- Produção: `wp-content/plugins/anthares-pix-sales/includes/65-leitura-beta.php` comparado byte a byte com `main` após merge: `PRODUCTION_MATCHES_GITHUB_MAIN=yes`, SHA256 `59984d4719ad3ad1f389b20215410a5e081a0eaf00b6ed77f57ed2f788a26713`.
- WordPress real: `BETA_FUNCTION_LOADED=yes`, `ANTHARES_ROLE_EXISTS=yes`, `ANTHARES_USERS_CHECKED=1`, `ANTHARES_ELIGIBILITY=PASS`.
- Integração: `ANTHARES_EDIT_CONTOS_CAP=yes`, `HOME_PROFILE_LEVEL=1`, `HOME_BETA_SECTION_ENABLED=yes`, `BETA_OFFER_FULL_GATE=yes`.
- Backup privado em Hostinger confirmado. Clone/arquivos temporários removidos. Nenhum arquivo de trabalho no PC. Não houve criação de ofertas ou transferências reais de Runas.

## Reconciliação e limite
O primeiro comando de implantação retornou erro de controle externo 500 após possíveis efeitos. A operação **não foi repetida**. Leitura posterior confirmou arquivo alterado, backup e lint; validação WP-CLI e comparação byte a byte confirmaram o estado final.
A regra de acesso está implantada e testada. Interação manual de publicação de um conto/transferência real de Runas não foi realizada para evitar teste financeiro ou conteúdo público não solicitado.
Os workflows automáticos que acionariam runner Windows foram evitados por `[skip ci]` nos commits e substituídos por QA externo.
Leases da área encerrados. Não sobrescrever se a fonte ou produção mudar.
