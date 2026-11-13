# A1 ReDroid firstboot prepared; zero OCI compute hosts available
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: none (firstboot simulated and linted, no instance available)
JOB: ARA 70e3eab950e301d6f6de0325d4456e73; ARA 10c593b72d727a390bcb06a942dc5d9a; ARA 3110f8f0123e7ab9b17ba6a09ae09bf8
COMMIT: branch feat/oci-a1-redroid-safe-firstboot-20261113
SUPERSEDES: test-hub/findings/20261113-oci-a1-existing-public-locked-egress-proven.md

## Objetivo
Preparar o primeiro boot da futura máquina Always Free A1 de modo que Linux ARM64 instale o container ReDroid com persistência e mantenha ADB na interface local.

## BASELINE_PROVEN
Repo main contém watcher OCI com capacidade real A1 `OUT_OF_HOST_CAPACITY`, rede existente elegível para `LOCKED_PUBLIC`, firewall TCP/22 /32 sem outras portas, 12 testes aprovados.

## FAILED_AVOIDED
Não iniciar Android sem binder no kernel; não expor ADB em 0.0.0.0:5555; não sobrescrever container/dados existentes; não inserir segredos, credenciais MacroDroid/Kwai ou chaves OCI em cloud-init; não trocar publicadores Neon; não criar máquinas pagas.

## TEST_VALIDITY
A configuração YAML foi parseada com PyYAML e transformada em OCI user_data Base64. O conteúdo Bash derivado foi analisado com Git Bash `-n`, `REDR0ID_BOOTSTRAP_BASH_SYNTAX=PASS`. Suíte Python isolada (sem arquivos persistidos no PC) passou com `TESTS 15 FAILURES 0 ERRORS 0`. `CLOUD_CONFIG_ENCODED_MATCH True`, `LOCAL_ONLY_ADB True True`. **Não houve execução real de cloud-init em VM**.

## SUCCESS_SIGNAL
Depois da implantação cloud efetiva: em Ubuntu 24.04 aarch64 a primeira inicialização deve carregar `binder_linux`, instalar Docker, preservar `/var/lib/anthares-redroid/android-data`, executar container `redroid/redroid:12.0.0_64only-240527`, escutar ADB somente `127.0.0.1:5555` e registrar `ANTHARES_REDR0ID_CONTAINER_RUNNING_LOCALHOST_ONLY`. MacroDroid, Kwai e confirmação Neon demandam provas posteriores independentes.

## FAILURE_SIGNAL
`OUT_OF_HOST_CAPACITY`, Actions sem secret/vars ou bootstrap que não encontra `binder` deixa Item 8 pendente. Qualquer ADB exposto publicamente inviabiliza implantação. Logs de cloud-init não são prova de Kwai autenticado nem publicação.

## Consequência
Firstboot preparado, sem custo e sem efeitos. Não habilitar publicação Kwai nem declarar ReDroid operacional até testes em VM gratuita real, instalação dos apps e failover de publicação.
