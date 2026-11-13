# OCI A1: rede pública existente com ingresso estritamente restrito
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: none (OCI API real consultada; nenhuma VM criada)
JOB: ARA 0e0f5921a14847053b2c4e26cd5f0757; ARA 3237c24888885611d6db0b7d0dc0a1bc
COMMIT: branch fix/oci-a1-safe-free-public-egress-20261113
SUPERSEDES: test-hub/findings/20261113-oci-a1-watcher-signer-network-guard-proven.md

## Objetivo
Aproveitar a rede OCI já provisionada sem criar NAT Gateway, mantendo o provisionamento eventual de VM ReDroid dentro da política de custo zero e sem exposição de portas Android.

## BASELINE_PROVEN
Monitor real autenticado consulta capacity: `OUT_OF_HOST_CAPACITY` para A1 e E2, 0 VMs. O monitor anterior, com `assign_public_ip=False`, verificava somente sub-rede privada + NAT e bloqueava corretamente a rede pública existente.

## FAILED_AVOIDED
Sub-rede Android `anthares-android-subnet` com Internet Gateway, sem NAT. Sem IPv4 público, a futura VM seria sem acesso de saída. Alternativa segura: IP IPv4 público efêmero (gratuito segundo a documentação pública Oracle), com firewall restrito a uma única regra TCP/22 de um CIDR /32 e egress IPv4, sem acesso público às portas de ReDroid/ADB. Nenhum recurso de rede existente foi alterado e nenhuma VM criada.

## SUCCESS_SIGNAL
OCI `VirtualNetworkClient`: `anthares-android-subnet` com route default Internet Gateway, única security list `anthares-android-ssh-locked`, ingress SSH TCP/22 restrito a /32, egress IPv4; `safe_instance_network_mode(...)=LOCKED_PUBLIC` em teste real. Python unit tests: `WATCH_NETWORK_TESTS 12 FAILURES 0 ERRORS 0`, verificando também que SSH público 0.0.0.0/0, ingress extra e porta ADB 5555 são recusados.

## FAILURE_SIGNAL
Qualquer nova regra de ingresso, rota, opção de gateway ou security list não homologada provoca `NETWORK_EGRESS_OR_INGRESS_GUARD` antes de `ComputeClient.launch_instance`. `OUT_OF_HOST_CAPACITY` e ausência de OCI Actions Secret/Vars continuam impedindo execução contínua e implantação do Android.

## TEST_VALIDITY
Consulta e testes somente leitura, sem criar NAT, IP, máquina ou serviço pago, sem alterar roteamento do Kwai. O código de monitor permite `assign_public_ip=True` apenas após guarda rígida; a criação efetiva de host e instalação de ReDroid/MacroDroid não foram testadas.

## Consequência
Pode-se reaproveitar a rede existente para o provisionamento automático quando houver capacidade A1, sem custear NAT. A implementação continuará desarmada até autenticação GH Actions autorizada, verificações de quota e reconciliação dos publicadores. ReDroid e Kwai em nuvem seguem pendentes.
