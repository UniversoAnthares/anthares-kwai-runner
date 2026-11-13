# ReDroid ARM64: manifesto imutável para bootstrap OCI A1
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: none (sem VM disponível)
JOB: ARA b4ea4a5d3a76a2c45e7fbe5b101cee5d; ARA 84d0fffb4c81338daafb78acdc6454ba
COMMIT: branch fix/oci-a1-redroid-arm64-digest-pin-20261113
SUPERSEDES: test-hub/findings/20261113-oci-a1-opc-retry-token-qa.md

## Objetivo
Impedir que uma alteração futura de tag Docker substitua sem revisão a imagem ARM64 do ReDroid utilizada pelo bootstrap da instância Always Free.

## BASELINE_PROVEN
A1 1 OCPU/6GB continua OUT_OF_HOST_CAPACITY, zero VMs. Bootstrap Ubuntu cloud-init com Docker, binder e ADB apenas no localhost já estava preparado em main; ainda não executado em VM.

## FAILED_AVOIDED
A imagem do bootstrap era referenciada pela tag mutável `redroid/redroid:12.0.0_64only-240527`. Agora usa manifesto ARM64 verificável `redroid/redroid@sha256:3c7f9450188226bf8042c0159b9b38abe2106f1ceb0dfa45fae1cbc6409cd9bb`. O cliente do monitor recusa cloud-init que não contenha o digest aprovado.

## SUCCESS_SIGNAL
API pública Docker Hub `/v2/repositories/redroid/redroid/tags/12.0.0_64only-240527`: digest ARM64 corresponde ao pin e difere do AMD64; 18 testes Python PASS, zero falhas; YAML parseado; Bash -n PASS.

## FAILURE_SIGNAL
Docker pull falha, módulos binder faltam, ou nenhuma VM OCI A1 disponível; todas são condições pendentes. A validação de manifesto/tag **não comprova** ReDroid executado e não autoriza Kwai em produção.

## TEST_VALIDITY
Testes foram apenas sintáticos/contratuais, com consulta pública Docker Hub, sem instalações, recursos pagos, download do container ou posts Kwai. Repetir o ciclo de testes em VM real antes de promover Android de contingência.

## Consequência
A futura VM buscará bytes específicos do manifesto ARM64 aprovado. A autenticação/ativação GitHub Actions e a disponibilidade A1 ainda são bloqueios de infraestrutura; MacroDroid e Kwai requerem homologação independente.
