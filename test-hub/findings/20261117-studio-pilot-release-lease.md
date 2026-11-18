# Studio: release restrito do G4 para conta autorizada
STATUS: RUNNING
DATE: 2026-11-17
AREA: anthares-studio/production/configured-pilot-rollout
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g4-user106-pilot-release-20261117
SOURCE: PR #321 HEAD 2693c15293a9483a92ff928ae11af6b0088ebd82
BASELINE_PROVEN: Hostinger plugin original SHA 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf. Studio PHP abb62797f3f3cf1ed6e32acaf45bfade3fbc5a75d1effb666ad6bf93e699968b; JS 65f51b87ad599258270f4a2264ef998a43866271882751d9d3bab1d69c889a2a. Code 72/72 Python+PHP lint+V8+manifest+orchestrator.
FAILED_AVOIDED: sem mutação de conteúdo REST autenticado após bloqueios da ferramenta; sem uso de navegador autenticado recusado; sem alterar Estúdio legado, pagamentos ou ACF.
SCOPE: aplicar apenas 2 arquivos do novo plugin anthares-studio já validados, backup de ambos, ativar apenas ID 106 na opção individual anst_pilot_writer_ids; escrita geral continua fechada e ACF desativado. Verificar hashes e resultado administrativo via WP-CLI sem editar conteúdo autoral.
SUCCESS_SIGNAL: arquivos com hashes de HEAD exata, listagem piloto contendo somente [106], ACF OFF e plugin original intacto.
FAILURE_SIGNAL: HEAD ou hashes divergentes, opção preexistente conflitante, erro de migração/lint, original modificado; executar rollback de arquivos e configuração.
TEST_VALIDITY: instalação de código e opção equivale a deploy; não prova CRUD autenticado, domínio visual ou preenchimento das 188 ferramentas.
LEASE: exclusivo de rollout G4, prazo de até 30 minutos, sem sobreposição com outras publicações; encerrar com novo finding.
