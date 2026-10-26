# WordPress Home22 — metabox de gênero validado em CI e integrado ao GitHub
STATUS: PARTIAL
AREA: wordpress
DATE: 2026-10-26
RUN: https://github.com/UniversoAnthares/anthares-wordpress/actions/runs/40321864247
JOB: 121568534169 (Home22) / 121568536168 (manifest)
COMMIT: 518e7595f2b2f39873f274fbb3855969f9424622
SUPERSEDES: test-hub/findings/20261026-0801-lease-wordpress-home22-genre-editor.md

## Lease encerrado
OWNER: ChatGPT
JOB: HOME22-GENRE-EDITOR-20261026
PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/201
Estado: PR #201 merged por squash para main; metabox conferido no blob canônico.

## Resultado
BASELINE_PROVEN: recomendação Home22 previamente implantada e 9/9 regressões CI (PR #200).
FAILED_AVOIDED: não criou classificação especulativa de 127 contos; não repetiu acesso de listagem de contos bloqueado por política de segurança.
SUCCESS_SIGNAL: metabox editorial `genero` no código para contos; nonce; capacidades `edit_others_posts` + `edit_post`; 5 gêneros, saneamento/normalização, proteção de autosave, revisão, entradas inválidas, idempotência. A codificação é lida pelo matching existente.
CI: run 40321588807 sucesso, PHP lint sem erro e 19/19 testes PASS com `OK | item 22: 19 verificações sem operações externas`; run 40321588809 sucesso QA manifesto; após atualizar evidência no relatório, run 40321864247 sucesso + run 40321864353 sucesso.
TEST_VALIDITY: testes isolados não modificaram dados reais; CI no HEAD da PR; blob resultante rechecado em main.
FAILURE_SIGNAL: nenhum dos casos de PHP ou manifesto falhou.
QA CLONE: tentativa auxiliar de git clone via ARA ficou incerta por conectividade; processo e diretório temporários foram reconciliados e encerrados, sem teste válido; CI oficial substitui esse harness.

## Limite e consequência
**PROVEN: código em main + 19/19 QA de comportamento + premerge manifest.**
**NOT PROVEN: implantação do novo metabox no WordPress/Hostinger e classificação editorial de contos reais.**
Metadados do catálogo não foram alterados. Home continua funcionando com interesses existentes e fallback sem gêneros. A listagem de contos por SSH já encontrou recusa de segurança da plataforma; não contornar.
A próxima operação autorizada deve comparar o SHA vivo com o blob de main, preservar backup, coordenar deploy e testar editor autenticado antes de anunciar produção. Para classificar, analisar o texto integral e obter decisão editorial fundamentada, evitando inferências por título.
