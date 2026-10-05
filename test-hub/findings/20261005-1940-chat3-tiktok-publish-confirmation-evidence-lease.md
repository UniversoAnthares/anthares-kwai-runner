# CHAT 3 lease — TikTok publish confirmation evidence
STATUS: RUNNING
AREA: tiktok-publish
DATE: 2026-10-05
RUN: pending
JOB: pending
COMMIT: 7d73f1c6ddb5b1b741f960e2149e3b1cf8eaa86c
SUPERSEDES: none
LEASE_OWNER: CHAT 3 — TikTok produção/sessão/publicação real/escala
LEASE_START: 2026-10-05T19:40:41-04:00
LEASE_EXPIRES: 2026-10-05T20:05:41-04:00

BASELINE_PROVEN: o workflow privado anthares-tiktok-owned-youtube.yml já exige evidência local confirmed antes de chamar /job/complete; o controlador snapshot v12 exige publication_started e remote_id ou confirmation_evidence para confirmação positiva; estados ambíguos já seguem para UNCERTAIN.
FAILED_AVOIDED: não inferir publicação a partir de workflow verde; não afrouxar a guarda central; não tocar em tiktok-session, atualmente bloqueada por dependência Cloudflare; não executar publicação real enquanto sessão/identidade não estiverem PROVEN.
SUCCESS_SIGNAL: o chamador privado envia confirmation_evidence explícita e não vazia somente a partir da evidência de publicação já validada quando remote_id estiver ausente, preservando o caminho remote_id; arquivo permanece sintaticamente válido e sem redução das guardas existentes.
FAILURE_SIGNAL: confirmação central ainda puder ser solicitada sem remote_id e sem confirmation_evidence; evidência puder ser fabricada sem confirmed local; workflow ficar inválido; contrato central divergir do payload.
TEST_VALIDITY: alteração estática e fail-closed no chamador privado, validada contra o contrato PROVEN do controlador e o blob atual do workflow; nenhuma sessão, publish request ou post real será disparado por este experimento.

## Objetivo
Adaptar o chamador TikTok ao contrato fail-closed do ledger sem alterar o controlador e sem executar publicação enquanto a sessão está bloqueada.
