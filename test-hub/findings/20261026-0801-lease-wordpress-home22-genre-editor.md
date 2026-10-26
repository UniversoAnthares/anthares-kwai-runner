# Lease WordPress Home 22 — metadados editoriais de gênero
STATUS: RUNNING
AREA: wordpress
DATE: 2026-10-26
RUN: none
JOB: HOME22-GENRE-EDITOR-20261026
COMMIT: 7f659197e724c9080040fb92057fe1d115fb3cc9
SUPERSEDES: none

## Propriedade e prazo
OWNER: ChatGPT
SCOPE: anthares-wordpress/anthares-pix-sales/includes/58-sorteio-home.php, qa/test-home-item22.php, docs/home-item22-recomendacao-generos-20261025.md
EXPIRES: 2026-10-26T12:31:00Z (max 30 min)
Não modificar sistemas CORTES nem o banco editorial sem evidência e autorização.

## Hipótese de trabalho
BASELINE_PROVEN: Home22 recomenda por interesses e gênero em QA, CI 40259186493 e 40259188924 success em main 7f659197e724c9080040fb92057fe1d115fb3cc9.
FAILED_AVOIDED: sem gênero editorial nos 127 contos; não preencher metadata por palpite ou burlar bloqueio de segurança de acesso ao WordPress.
SUCCESS_SIGNAL: painel editorial com nonce, capability, normalização e persistência de campo compatível; lint e testes comportamentais; PR com evidência.
FAILURE_SIGNAL: testes PHP vermelhos, regressão de Home, permissão indevida ou PR não reconciliável.
TEST_VALIDITY: confirmar SHA da branch, lint e QA sob PHP, cobertura de manifesto e estado da implantação antes de classificar produção.
