# OCI Always Free A1: durable request idempotency within Oracle retry window
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: none (read-only capacity OCI and Python regression tests, no Compute launch)
JOB: ARA dc827af30b7b88d54ad60d6903aa621d
COMMIT: branch fix/oci-a1-free-launch-idempotency-20261113
SUPERSEDES: test-hub/findings/20261113-oci-redroid-firstboot-userdata-staged.md

## Objetivo
Evitar lançamentos duplicados de VM A1 gratuita quando a API OCI concluir a criação, porém a resposta HTTP for perdida ou retornar erro temporário.

## BASELINE_PROVEN
Monitor OCI com capability/shape guard, execução sem chave armazenada no repositório, firewall SSH /32, cloud-init ReDroid, e 15 testes PASS. Relatório OCI em 13/11/2026 10:49 UTC: A1 1 OCPU/6GB OUT_OF_HOST_CAPACITY, zero instâncias no compartimento raiz.

## FAILED_AVOIDED
Ausência de token de idempotência em ComputeClient.launch_instance; uma repetição de chamada após perda de resposta HTTP poderia duplicar um recurso A1, ainda que o cron seja sequencial. O script usa agora UUIDv5 determinístico por tenancy/subnet/região/VM, com opção opc_retry_token nativa (Oracle: janela de 24h), e mantém NoneRetryStrategy e inventário de recursos anterior à criação.

## SUCCESS_SIGNAL
Regressão Python: `OCI_A1_TESTS 17 FAILURES 0 ERRORS 0`; testes novos conferem UUIDv5 estável, mudança de token para tenant/subnet diferentes e argumento opc_retry_token recebido por mock de ComputeClient.launch_instance. Documentação atualizada; nenhum segredo em repo.

## FAILURE_SIGNAL
Monitor GitHub Actions permanece desativado sem OCI_A1_WATCH_AUTH_JSON e OCI_A1_WATCH_ENABLED. A capacidade OCI segue OUT_OF_HOST_CAPACITY. O OPC retry token expira após 24 horas e não substitui reconciliação, nem comprova uma VM ou ReDroid ativo.

## TEST_VALIDITY
A execução de testes foi transitória em Python sem arquivos de trabalho, sem tocar a fila Kwai, sem criar a VM. A idempotência real do serviço Oracle não foi exercitada em uma criação real por indisponibilidade de capacidade. Testes são de contrato, com fonte da API OCI.

## Consequência
Ao aparecer capacidade, a máquina pode ser provisionada com deduplicação suportada pela API, dentro dos guards de orçamento/capacidade/rede. Para marcar o item 8 concluído ainda são necessários autenticação no runner GitHub, VM real, sucesso do cloud-init, apps MacroDroid/Kwai autenticados e failover de publicação sem duplicação.
