# TikTok LIVE — sessão primária Cloudflare OIDC bloqueada (401)
STATUS: PARTIAL
AREA: tiktok-live-primary-account-readonly
DATE: 2026-11-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42864768551
JOB: 130000034814
COMMIT: 12e57568d588287481c29c1e4cb2e52999c6f090
SUPERSEDES: test-hub/findings/20261110-tiktok-live-primary-account-readonly-running.md
LEASE_AREA: tiktok-live-primary-account-readonly
LEASE_STATUS: CLOSED

## Resultado
- Inicialmente workflow rejeitado antes de qualquer job por context inválido (runner.temp no job.env); corrigido em commit 12e5756.
- Job posterior executou e fez GET somente leitura na rota OIDC já existente /tiktok/session-state. Resposta HTTP 401: TIKTOK_PRIMARY_SESSION_AUTH_DENIED=1; job encerrou com exit 41.
- Chromium não iniciou na tentativa negada, sessão não foi lida e nenhuma LIVE foi criada.
- Recusa 401 é controle de autorização, não cota. Nenhuma tentativa com outra identidade, ref, credencial ou canal é autorizada para contornar essa negativa.

## Consequência
Verificação LIVE da conta @universo.anthares nesta branch é AUTH_DENIED; elegibilidade indeterminada. A conta secundária @lucasrosalem4 teve Studio e LIVE Center acessíveis em run 42863880530, sem botão RTMP. Para completar transmissão requer autorização de ingestão do próprio TikTok e rota legítima de servidor/chave ou parceiro aprovado. Não alegar LIVE operacional.
