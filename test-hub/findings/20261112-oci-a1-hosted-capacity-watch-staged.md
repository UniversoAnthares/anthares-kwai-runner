# Oracle A1 capacity watcher + MacroDroid phone status probe — staged
STATUS: PARTIAL
AREA: android
DATE: 2026-11-12
RUN: none
JOB: none
COMMIT: branch feat/oci-a1-cloud-android-standby-20261112
SUPERSEDES: none

## Objetivo
Reduzir dependência futura do PC: agendar em GitHub Actions o teste de capacidade Always Free Oracle A1 a cada quatro horas, com opção de única alocação protegida, e criar uma macro de observabilidade Kwai/Neon no Android físico.

## BASELINE_PROVEN
Consulta `ComputeClient.create_compute_capacity_report` em `sa-saopaulo-1` retornou `OUT_OF_HOST_CAPACITY` para A1 1 OCPU/6 GiB e E2.1.Micro. Zero instâncias A1/boot volumes. Fonte: `UniversoAnthares/anthares-governance/OCI_ANDROID_A1_CAPACIDADE_20261112.md`. Fila Neon tem autenticação móvel específica `kwai-mobile-primary` e pacing no endpoint `kwai-physical-stats`. O publicador principal existente utiliza Android físico e o MEmu é reserva.

## FAILED_AVOIDED
Sem novas tentativas de lançar VM com capacidade negada; sem recurso pago; sem iniciar segundo consumidor de fila; sem alterar Kwai principal ou publicar cortes. Sem copiar chaves para arquivos ou logs. Proteção GitHub exige pull request, por isso nenhuma alteração na `main` antes da revisão.

## TEST_VALIDITY
Foi realizado teste de compilação sintática do novo Python em processo transitório sem persistir artefatos no PC: `CLOUD_WATCH_PYTHON_SYNTAX=PASS`. YAML parseado com PyYAML: `CLOUD_WATCH_WORKFLOW_YAML=PASS`. MacroDroid Macro Builder validou `VALID`, 1 trigger, 2 ações, 1 constraint. A execução OCI por runner GitHub e o import no Android **ainda não foram realizados**.

## SUCCESS_SIGNAL
Para considerar *staging* entregue: branch com script, workflow cron 4h, testes, documentação; macro importável de consulta, desativada e sem token embutido. Para considerar operacional: job Github `SUCCESS` autenticado, `ANTHARES_A1_CAPACITY=` comprovado e no futuro, se for `AVAILABLE`, Linux A1 criada com `ANTHARES_A1_STATE=INSTANCE_CREATED_`. Ainda depois disso são necessários os testes de binderfs, ReDroid, MacroDroid e publicação/contingência no Kwai.

## FAILURE_SIGNAL
Falta de GitHub Actions secret/variables, quota CI, política OCI ausente, report `OUT_OF_HOST_CAPACITY`, ausência de Ubuntu 24.04 ARM ou falha nos controles de 200 GiB impedem alocação; falha MacroDroid/token impede consulta no Android. Nenhuma dessas falhas autoriza remover controles, usar outra credencial sem autorização, ou duplicar jobs Neon.

## Resultado
**PARTIAL:** código de monitor+alocação guardada e macro de consulta estão criados; o GitHub ainda exige PR e a rotina está desarmada por falta de segredo/variáveis autenticadas. Link MacroDroid `https://macrodroidlink.com/m/YhAvtvS2oufP`, com expiração em 20/11/2026 UTC. Objetivo de Android em nuvem totalmente autônomo segue pendente.

## Consequência
Continuar com revisão/merge controlado, provisionamento seguro de credenciais via GitHub Actions ou OCI WIF, execução real hospedada; depois implementar consumidor MacroDroid no aparelho com token local, lease Neon e confirmação comprovada. Preserve Android físico/MEmu atuais e estados UNCERTAIN; nunca confundir estágio de código com implantação.
