# Studio G4 — permissao unificada para todas as gravacoes
STATUS: PARTIAL
AREA: wordpress/studio/g4-private-admin-write
DATE: 2026-11-17
JOB: studio-g4-private-admin-write-20261117
COMMIT: 4527966029ee4c9831a722cecd936c34843107d5
PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/316
SUPERSEDES: 20261117-studio-g4-parity-rest-frontend-admin-guard.md

## Ajuste complementar
A revisao da PR identificou que `/lesson/{section}` usa `anst_lesson_permission` distinto da permissao das demais rotas, permitindo atualizar links de aula ao papel Anthares quando `anst_writes_enabled=1`. Por isso, a PR centralizou a dupla verificacao de escrita em `anst_write_pilot_gate()` e passou a reutiliza-la tanto em `anst_permission` quanto em `anst_lesson_permission`.

## Garantias no codigo do piloto
- `anst_writes_enabled=0`: leitura e consultas continuam; POST/DELETE recebem 423.
- `anst_writes_enabled=1` e `anst_pilot_admin_only=1` (padrao): somente `manage_options` pode gravar; todos os demais recebem 403 no gate, inclusive rota das aulas.
- `anst_pilot_admin_only=0`: permite ampliar acesso apos autorizacao e testes (permanece verificacao primaria `anst_can_use` e permissao especial de gerenciamento de aulas).
- `ANST_ACF_RUNTIME_APPROVED` permanece false por padrao na branch; ACF OFF em producao.
- Nenhuma alteracao em /estudio ou dados dos autores.
- Os testes unitarios estaticos e fixture foram ampliados para abranger gate compartilhado e preservacao de acoes JS.

## Evidencias e limites
Inspecao estatica: 10 assercoes basicas PASS, contrato de 14 acoes JS da origem presentes e 16 funcoes de tela/edicao presentes, 665/665 caminhos no manifesto GitHub sem duplicacao.
A execucao do teste Python e do PHP lint para o HEAD atual, a validacao REST em banco isolado, os screenshots G4 e um backup com restauração verificada seguem pendentes. Nenhum deploy, merge, ligacao de escrita ou ACF realizado nesta rodada.
Uma chamada remota que tentava clonar codigo para QA foi bloqueada pela ferramenta de seguranca; nao usar outra rota para contornar essa recusa.
