# Anthares Studio G5 — autorização ACF externa obrigatória
STATUS: PROVEN
AREA: wordpress/studio/g5
DATE: 2026-11-17
RUN: Hostinger SSH / checkout efêmero de código (sem alteração do WordPress produtivo)
JOB: studio-acf-dual-approval-guard-20261117
COMMIT: 2e2935f9cd8f6d95cb9d64a79ca871d93267736b
PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/315
SUPERSEDES: none

## Objetivo
Garantir que a aprovação para ativar o armazenamento ACF exija configuração externa, além de `anst_acf_runtime_enabled=1`.

## Achado
O código original de integração definia `ANST_ACF_RUNTIME_APPROVED=true` dentro do plugin. A condição de aprovação externa estava satisfeita automaticamente.

## Correção preparada (sem deploy)
O plugin passa a definir `ANST_ACF_RUNTIME_APPROVED=false` quando ausente; permite aprovação explícita anterior ao carregamento. A função `anst_acf_runtime_enabled()` mantém a exigência de `ANST_ACF_RUNTIME_APPROVED===true` E da opção interna igual a `1`. O teste estático de regressão rejeita a definição padrão `true`.

## Evidências QA executadas
- Checkout privado e efêmero no Hostinger; commit exato acima.
- `python3 -m unittest discover -s anthares-studio/tests` => **49 testes, OK**.
- `/opt/alt/php83/usr/bin/php -l anthares-studio/anthares-estudio.php` => **PASS**.
- `/opt/alt/php83/usr/bin/php -l anthares-studio/tests/integration/g5-runtime-fixture.php` => **PASS**.
- `python3 qa/manifest-coverage-preflight.py --check` => **PASS, 665/665**.
- `/opt/alt/php83/usr/bin/php qa/anthares-orchestrator-qa.php` => **11 verificações PASS**.
- Checkout efêmero removido por trap de limpeza. `anthares-estudio` original e dados produtivos não foram alterados.
- Uma tentativa inicial de lint com PHP CLI padrão 7.4 falhou por incompatibilidade do PHP do site; corrigido para PHP 8.3, resultado PASS.

## Limites e consequência
Comprovação limitada a testes unitários/estáticos e sintaxe do código da PR #315. Exige ensaio de ativação ACF com e sem cada fator no banco MariaDB de homologação, seguida dos gates G4/G5 completos. Não autoriza merge nem deploy, alterações de CPT, migração ACF, alteração de flags ou publicação da página privada /studio. Código permanece em PR draft baseada na PR #314. O novo Studio em produção continua com `anst_writes_enabled=0`.
