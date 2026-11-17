# G5 QA isolada: fixture PHP de CPTs administrativos

STATUS: RUNNING
DATE: 2026-11-17
AREA: anthares-studio/g5/private-cpt-admin-qa
JOB: studio-g5-cpt-php-runtime-fixture-20261117
OWNER: ChatGPT / OBSERVATORIO IPB
SOURCE: UniversoAnthares/anthares-wordpress PR #317 HEAD d6697afb74a11d09eb1589cdd84085867279e0b7.
PEER: GitLab branch feat/studio-g5-private-cpt-admin-20261117 404.
BASELINE_PROVEN: PR #317 draft, quatro CPTs privados com capacidades manage_options; mock PHP 8.4 PASS com 76 asserções (4 registros, 19 por registro).
FAILED_AVOIDED: nenhum teste de escrita em banco produtivo, nenhuma alteração no plugin legado, nenhuma chamada de navegador host bloqueada.
SCOPE: alterar exclusivamente anthares-studio/tests/test_acf_contract.py na PR #317, adicionando teste dinâmico que extrai a função de registro diretamente do código sob teste e roda stub PHP em processo isolado sem bootstrap WordPress e sem rede; sem arquivo novo no repositório WordPress.
SUCCESS_SIGNAL: teste PHP passa com 4 CPTs e 76 verificações, falha se show_ui, private ou primitive caps divergirem.
FAILURE_SIGNAL: PHP quebra ou retorno difere; nenhum deploy/merge após falha.
TEST_VALIDITY: esta fixture verifica o contrato de registro de CPTs sem WordPress real; a homologação no WordPress continua pendente.
ROLLBACK: reverter apenas o commit de teste na PR #317.
