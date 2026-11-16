# Anthares Studio — Gate G1: backup restaurado, baseline de interface parcial

STATUS: PARTIAL
AREA: studio-g1-backup
DATE: 2026-11-16
RUN: Hostinger MariaDB isolado, rede desabilitada
JOB: studio-g1-backup-20261116-1527
COMMIT: anthares-wordpress/main 40820c15388f584beca830feec3200a135833b28
SUPERSEDES: test-hub/findings/20261116-1523-lease-studio-g1-baseline-backup.md

## Resultado PROVEN — dados e integridade
- Backup restrito a `anthares-private-storage/studio-g1-backup-20261116-1527/`, fora do public_html e sem armazenamento no PC.
- `wordpress-consistent.sql.gz`: 45.067.215 bytes, exportação `wp db export - --single-transaction --quick --skip-lock-tables`.
- `anthares-estudio-original.tar.gz`: 151.917 bytes, inclui sete arquivos originais.
- `backup-sha256.txt` confirmado com sha256sum -c; gzip -t e tar -tzf aprovados.
- Restauro em MariaDB 11.8 isolado por socket e `--skip-networking`, sem tocar em banco compartilhado: 217 tabelas, 40 posts internos `aest_*` publicados, 31 itens na lixeira, 7 `_aest_delta`.
- `restore-verification.txt` armazenado no backup privado. Servidor temporário finalizado e datadir de ensaio removido no cleanup.
- SHA-256 do PHP original manteve `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf` antes/depois. Zero referências `/uploads/`/attachment em postmeta dos CPTs legado.
- Documentação G0: PR https://github.com/UniversoAnthares/anthares-wordpress/pull/302 mesclada no main; QA `QA_MANIFEST_PREFLIGHT=PASS auditable=629 assigned=629 exactly_once=yes` e orquestrador PHP todos PASS.

## G1 PARCIAL — evidência visual
- Browser conectado identificou aba autenticada /estudio com os seis itens globais e nove grupos internos; capturas do titular e HTML/SHA dos assets disponíveis.
- Matriz de screenshots desktop, mobile, 0/1/N projetos e todas as subabas ainda pendente. A auditoria de paridade e ativação de /studio permanecem BLOQUEADAS.

## Próxima ação segura
Preparar cópia de código em branch GitHub isolada, apenas como snapshot literal de origem, para permitir diff de isolamento. Nenhuma ativação, mudança no legado, nova rota, ou escrita em dados reais antes do aceite G1 visual e dos testes G2.
