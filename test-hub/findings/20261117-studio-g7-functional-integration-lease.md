# Studio G7 — integração funcional de domínio e interface
STATUS: RUNNING
AREA: anthares-studio/production/G7-story-domain
DATE: 2026-11-17
OWNER: ChatGPT CURSO ESCRITA CRIATIVA
JOB: anst-g7-functional-20261117
BASELINE_PROVEN: G4 implantado, G5 415/415 alvos ACF preenchidos, opção ACF runtime 1, plugin antigo intacto. PR #318 G7 em branch isolada já existe.
FAILED_AVOIDED: não substituir JS por versão antiga que remove proteção de perda do Delta Quill. Mesclar 3 vias contra HEAD G4 atual; nenhuma mutação em autoria dos projetos.
SUCCESS_SIGNAL: rotas story/entities, story/relations, story/curves expostas, interface G7 integrada, PHP e JS parse, backup de reversão.
FAILURE_SIGNAL: conflito não resolvido, PHP syntax fail ou mudanças no plugin antigo; rollback do novo plugin.
TEST_VALIDITY: confirmação de instalação e integridade mínima não equivale a homologação visual.
LEASE: 30 minutos máximo apenas arquivos anthares-studio, sem intervenção no PC e sem PR nova.
