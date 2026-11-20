# Lease - verificação pós-FTP /studio/
OWNER: ChatGPT / POST_FTP_SYNC_20261120
STATUS: ACTIVE
START_UTC: 2026-11-20T03:44:00Z
EXPIRES_UTC: 2026-11-20T04:14:00Z
SCOPE: QA pós-upload de três JS instalados pelo usuário. Somente uma aba de testes própria no Chrome CDP port 9241 e um projeto de teste identificado como QA-POST-FTP-20261120, com seus capítulos. Nenhum dado anterior.
PRECONDITIONS: live installed JS SHA256 match ZIP; 51/51 local Python tests PASS; /studio/ and /estudio/ HTTP 200.
ALLOWED: create/rename QA-only project; import 1 TXT and check immediate chapter updates across core and DOCX; cleanup only QA ids after verifying title/author/project. No public publishing, no emails, no other user account, no payments.
EXIT: delete fixture and verify 22 existing projects; close only QA tab, preserve user login; status CLOSED after report.
