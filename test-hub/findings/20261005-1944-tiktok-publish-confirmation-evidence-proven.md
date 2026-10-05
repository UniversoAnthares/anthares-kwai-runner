# TikTok caller envia confirmation_evidence fail-closed ao ledger central
STATUS: PROVEN
AREA: tiktok-publish
DATE: 2026-10-05
RUN: none
JOB: none
COMMIT: 0e9cf9f94d8d74e2d709cb1783dd8bc8ca1d4bcf
SUPERSEDES: test-hub/findings/20261005-1940-chat3-tiktok-publish-confirmation-evidence-lease.md

BASELINE_PROVEN: o workflow privado já exige evidence.confirmed antes de /job/complete; o controlador PROVEN exige publication_started e remote_id ou confirmation_evidence; caminho ambíguo de publisher permanece UNCERTAIN.
FAILED_AVOIDED: a guarda central não foi relaxada; confirmação não é inferida de workflow verde; tiktok-session não foi tocada; nenhum canário foi disparado enquanto sessão/identidade continuam bloqueadas.
SUCCESS_SIGNAL: quando existe remote_id real, ele continua no payload; quando remote_id está vazio, o chamador envia confirmation_evidence explícita derivada apenas do arquivo de evidência já confirmado; sem confirmation kind o fechamento falha.
FAILURE_SIGNAL: payload permitir confirmed=true sem remote_id e sem confirmation_evidence; alteração tocar outras guardas; ausência de fail-closed para evidence.confirmed.
TEST_VALIDITY: diff do commit mostra alteração restrita ao payload de /job/complete; simulação local dos casos remote_id, ui_success, render_ui_success e prova ausente confirmou os invariantes. Esta prova é de código/contrato e não equivale a publicação TikTok real.

## Objetivo
Adaptar o caller privado ao contrato fail-closed do ledger central sem alterar o controlador.

## Resultado
PROVEN em código. Commit 0e9cf9f94d8d74e2d709cb1783dd8bc8ca1d4bcf em UniversoAnthares/anthares-clipper altera somente o fechamento central: remote_id real continua preferencial; na ausência dele, confirmation_evidence é serializada a partir de campos seguros do publisher (confirmation e, quando disponíveis, confirmed_at/account/segment_id/source_id/caption/remote_url). Se confirmation também estiver ausente, o job permanece sem confirmação.

## Evidência decisiva
O diff do commit contém apenas o bloco de payload do step Confirm central queue publication. O controlador em 83695af aceita confirmação positiva somente com String(remote_id || persisted_remote_id || confirmation_evidence). A matriz local validou: remote_id -> aceito; ui_success -> confirmation_evidence; render_ui_success -> confirmation_evidence; evidence sem confirmation -> rejeitada.

## Consequência
LEASE tiktok-publish encerrado para esta lacuna. O canário real continua bloqueado por tiktok-session: GET central de sessão está 403 e o env-seed Render foi provado ausente/inutilizável. Próxima lacuna de publicação, depois da sessão, é a verificação independente do post/perfil antes de considerar PRODUCTION PROVEN.
