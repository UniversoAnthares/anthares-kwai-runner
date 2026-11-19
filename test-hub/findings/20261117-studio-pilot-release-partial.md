# Studio: release G4 restrito e acesso à página corrigidos
STATUS: PARTIAL
DATE: 2026-11-17
AREA: anthares-studio/production/configured-pilot-rollout
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g4-user106-pilot-release-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/321
COMMIT: 2693c15293a9483a92ff928ae11af6b0088ebd82
SUPERSEDES: test-hub/findings/20261117-studio-pilot-release-lease.md
BASELINE_PROVEN: novo plugin PHP SHA-256 abb62797f3f3cf1ed6e32acaf45bfade3fbc5a75d1effb666ad6bf93e699968b e JS SHA-256 65f51b87ad599258270f4a2264ef998a43866271882751d9d3bab1d69c889a2a. Antigo plugin SHA de referência 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.
FAILED_AVOIDED: sem escrita em projetos reais por REST autenticado/uso de navegador com restrição explícita. Sem alteração do legado nem ativação ACF.
SUCCESS_SIGNAL: arquivos instalados mudaram a partir do baseline; wp option get anst_pilot_writer_ids --format=json => [106]; wp eval com wp_set_current_user(106), anst_write_pilot_gate() => true; antigo plugin SHA intacto e ACF opção 0; backup persistente em /home/u566597497/.anthares-studio-rollback/g4-user106-20261118; página Studio ID 21383 alterada private -> publish, GET URL HTTP 200.
FAILURE_SIGNAL: fluxo real de criação/salvamento sem prova; manter G4 como implantação parcial até teste de ponta a ponta.
TEST_VALIDITY: prova da publicação e autorização backend WordPress, não equivale a teste REST autenticado do autor.
RESULT: DEPLOYED code G4 + option individual + page route; G4 E2E ainda OPEN.
NEXT: completar G5 ACF e G7 188 funções em processo separado; preservar PR #320/#321 e dados existentes.
LEASE: terminado, sem recursos temporários mantidos.
