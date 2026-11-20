# Lease - verificação pós-FTP /studio/
OWNER: ChatGPT / POST_FTP_SYNC_20261120
STATUS: CLOSED_SUCCESS
START_UTC: 2026-11-20T03:44:00Z
EXPIRES_UTC: 2026-11-20T04:14:00Z
SCOPE: QA pós-upload de três JS instalados pelo usuário. Somente uma aba de testes própria no Chrome CDP port 9241 e um projeto de teste identificado como QA-POST-FTP-20261120, com seus capítulos. Nenhum dado anterior.
PRECONDITIONS: live installed JS SHA256 match ZIP; 51/51 local Python tests PASS; /studio/ and /estudio/ HTTP 200.
ALLOWED: create/rename QA-only project; import 1 TXT and check immediate chapter updates across core and DOCX; cleanup only QA ids after verifying title/author/project. No public publishing, no emails, no other user account, no payments.
EXIT: delete fixture and verify 22 existing projects; close only QA tab, preserve user login; status CLOSED after report.

CLOSED_UTC: 2026-11-20T03:52:15Z
PRODUCTION_CHECK: three files live match FTP ZIP SHA256, /studio and /estudio HTTP200, 51/51 Python tests PASS.
AUTH_BROWSER: QA-only CDP tab 3DCF0B790D783BCE5284CFCB24FED09B confirmed authenticated, closed successfully; prior user's tab preserved.
UI_E2E: 1 chapter via new-chapter => core list 1, DOCX selector 1 without reload; bulk import TXT+MD 2/2 PASS => core 3 / DOCX 3 without reload; DOCX export+parse+preview+import => core 4 / DOCX 4 without reload.
CLEANUP: QA project 22014, children 22015..22018 deleted; database count IDs 22014-22018 zero; original published-project count 22 unchanged.
ALL_CHECKS_PASSED: production fix verified. Cross-account acceptance and commercial public publishing remain unexercised by design.
