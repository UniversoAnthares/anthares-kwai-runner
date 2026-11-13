# OCI Always Free — sub-rede e SSH prontos antes de haver capacidade A1
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: OCI read-only preflight; no Compute launch
JOBS: ARA 2c384269b48ffd1cd5629bf727e4d273; ARA 00825a70361e6c891912be6cb8ef8bc9; ARA 12e577bd5ffc01ee4900c20481ecb3bd
COMMIT: branch feat/oci-a1-provision-preflight-ssh-subnet-20261113
SUPERSEDES: test-hub/findings/20261113-redroid-portable-amd64-arm64-binder-reboot-contract.md

## BASELINE_PROVEN
GitHub Actions monitor autenticado #43458571942 terminou PASS, com 22 testes e `ANTHARES_A1_CAPACITY=OUT_OF_HOST_CAPACITY`. Criação de VM do cron continua desarmada (env imposto `OCI_A1_AUTO_PROVISION=0`). O segredo `OCI_A1_WATCH_AUTH_JSON` inclui só os cinco campos de OCI signer. O ramo antigo de launch exigia subnet_id e ssh_public_key no mesmo JSON e não tinha como alocar host.

## CHANGES
- Cliente `tools/oci_a1_capacity_watch.py`: `approved_subnet` procura exatamente a sub-rede `anthares-android-subnet` com CIDR `10.92.1.0/24` no compartimento raiz, bloqueia ambiguidade/desvio e recarrega por OCID; `approved_ssh_public_key` verifica tipo `ssh-ed25519`, Base64 e fingerprint SHA-256 pinado, lendo somente `infra/oci-android/approved-admin-ssh.pub`.
- A chave pública foi obtida da configuração SSH administrativa já autorizada pelo proprietário e versionada sem chave privada; divergências com overrides opcionais levam a `ValueError`.
- `approved_boot_access` exige `safe_instance_network_mode`; preflight roda mesmo em `OUT_OF_HOST_CAPACITY`; relata estado de rede e readiness, mantendo os guardas já existentes: singleton A1, storage 200GB, GH Actions sem provisioning, OPC retry token, seleção da imagem Ubuntu ARM64.
- Workflow monitora os campos e reexecuta testes via GitHub Actions a cada quatro horas, sem importar qualquer segredo SSH.

## SUCCESS_SIGNALS
- 21 testes Python PASS, 0 erros (ARA `2c384269b48ffd1cd5629bf727e4d273`).
- 6 testes Python PASS, 0 erros (ARA `00825a70361e6c891912be6cb8ef8bc9`).
- Fingerprint SSH da chave pública versionada corresponde ao hash autorizado no script; fonte é somente `ssh-ed25519.pub`, sem private.
- OCI real read-only: `OCI_REAL_PREFLIGHT READY`, sub-rede `anthares-android-subnet`, rede `LOCKED_PUBLIC`, SSH ed25519 e `OCI_AUTO_PROVISION OFF_READ_ONLY` (ARA `12e577bd5ffc01ee4900c20481ecb3bd`).
- A1 segue `OUT_OF_HOST_CAPACITY`; nenhuma VM criada.

## REMAINING_BLOCKERS
- Ainda requer uma VM realmente disponível, imagem Ubuntu ARM64, estoque e execução do cloud-init.
- O teste local OCI com credencial própria é independente da execução do GitHub Actions; validar novamente em runner hospedado ao integrar PR.
- Autenticação MacroDroid/Kwai e publicação com fila Neon lease sem duplicatas precisam de host e prova separada.
- Provisionamento automático não foi habilitado. Nunca tratar o relatório READY como VM criada ou sessão Kwai autenticada.
