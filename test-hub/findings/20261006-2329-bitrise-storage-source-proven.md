# Bitrise configuration storage diagnosis
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: 1f7e78595730327d344855b6a49b8b58bcfa4863
SUPERSEDES: none

## Objetivo
Determinar por que o projeto Bitrise está executando a configuração Android gerada pelo onboarding em vez do bitrise.yml versionado no repositório.

## Resultado
A configuração atualmente usada pelo projeto está explicitamente armazenada em Bitrise (Stored on Bitrise). O editor mostra a configuração armazenada localmente no Bitrise, com workflows gerados como build_apk e run_tests. O arquivo canônico bitrise.yml no repositório contém outra configuração: project_type: other, workflow primary e o smoke test compartilhado.

## Evidência decisiva
Screenshot do Workflow Editor em 2026-10-06 mostra no cabeçalho CI configuration • Stored on Bitrise e os Workflows gerados build_apk, run_instrumented_tests e run_tests.
O arquivo versionado bitrise.yml no commit 1f7e78595730327d344855b6a49b8b58bcfa4863 contém workflows.primary, ci/shared/provider-smoke.sh e deploy de ci-hub/bitrise/runtime.
Bitrise documenta que a configuração pode ser armazenada no Bitrise ou no repositório e que o editor permite trocar a fonte por Change storage.

## Consequência
A próxima ação deve ser trocar a fonte da configuração de Stored on Bitrise para o bitrise.yml do repositório. Não corrigir os workflows Android gerados no YAML armazenado no Bitrise. Depois da troca, executar o workflow primary e verificar o smoke test real do provider.