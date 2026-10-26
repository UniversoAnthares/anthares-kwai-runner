# Lease — navegador WordPress dedicado para Home22
STATUS: RUNNING
AREA: wordpress-auth-browser
DATE: 2026-10-26
RUN: none
JOB: HOME22-WP-AUTH-PROFILE-20261026
COMMIT: 518e7595f2b2f39873f274fbb3855969f9424622
SUPERSEDES: none

OWNER: ChatGPT
EXPIRES: 2026-10-26T13:23:00Z
SCOPE: D:\AntharsWork\browser-profiles\AntharesBrowserHub.ps1 e novo perfil AntharesWordPressAdmin; nenhum perfil CORTES ou Chrome pessoal.

BASELINE_PROVEN: WordPress code PR #201 merged; 19/19 QA. Browser Hub isolado sem perfil WordPress; AntharesGitLab CDP 9223 recebeu wp-login e Google accountchooser, não comprovou admin. Preflight local browser-profiles PASS.
FAILED_AVOIDED: não reutilizar conta Google não confirmada; não copiar cookies ou contornar recusa de SSH de ferramentas; não usar container de Kwai ou sessão pessoal.
SUCCESS_SIGNAL: criar perfil isolado no Hub, CDP 9234 loopback, preservar perfis prévios e habilitar login WordPress na própria instância; verificar sessão antes de implantar.
FAILURE_SIGNAL: interferir em perfil de outro serviço, CDP exposto, conflito/alteração concorrente, auth não comprovada.
TEST_VALIDITY: conferir hash antigo/novo, serviços não afetados, novo perfil isolado, navegador temporário fechado exceto login interativo explicitamente necessário.
