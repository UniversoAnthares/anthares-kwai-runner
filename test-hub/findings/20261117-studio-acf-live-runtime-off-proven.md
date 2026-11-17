# Anthares Studio — correção da ativação ACF prematura no piloto
STATUS: PROVEN
AREA: wordpress/studio/g5-live-safety
DATE: 2026-11-17
RUN: Anthares Remote → SSH Hostinger → WP-CLI PHP 8.3
JOB: studio-acf-live-runtime-remediation-20261117
COMMIT: none (opção WordPress exclusivamente)
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2645
SUPERSEDES: none

## Achado em produção
- Plugin `anthares-studio` ativo, versão 0.7.8-staging.
- Página WordPress `21383`, slug `studio`, status `private` (HTTP 404 para requisição pública não autenticada).
- `anst_writes_enabled = 0` confirmado imediatamente antes da alteração.
- `anst_acf_runtime_enabled = 1` confirmado imediatamente antes da alteração.
- Fonte instalada definia `ANST_ACF_RUNTIME_APPROVED=true` internamente e wp-config não continha essa definição.
- `wp eval 'echo anst_acf_runtime_enabled() ? "ACF_ON" : "ACF_OFF";'` => **ACF_ON**.
- PHP legado `anthares-estudio.php`: SHA-256 `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf` antes da intervenção, idêntico ao baseline de 16/11.

## Remediação aplicada
Única operação de escrita: `wp option update anst_acf_runtime_enabled 0` no WordPress Hostinger, que retornou `Success: Updated 'anst_acf_runtime_enabled' option.`

A verificação posterior com WP-CLI, executando a função real `anst_acf_runtime_enabled()`, respondeu **ACF_OFF**.

Não foram alterados `/estudio`, PHP, arquivos Quill, posts, metadados, páginas, opções de gravação ou migrações. O Studio permanece em página privada, com escrita bloqueada segundo o preflight `anst_writes_enabled=0`. Nenhum usuário teve conteúdo excluído. Nenhum processo foi reiniciado.

## Estado e próximos gates
- **PROVEN:** ACF OFF após alteração mínima, com confirmação funcional direta.
- **PENDENTE:** prova completa de paridade G4 com contas autenticadas, ACF ON em banco isolado com flag externa explícita, testes de evolução das entidades G7, rollback e publicação após aprovação.
- Código permanente de hardening preparado em PR [#315](https://github.com/UniversoAnthares/anthares-wordpress/pull/315) para impedir reativação apenas por opção.
- Valor anterior da opção: `1`; reversão exige autorização e condições G4/G5.

A ausência de novas gravações no banco durante esta inspeção não foi verificada com auditoria transacional e não deve ser alegada.
