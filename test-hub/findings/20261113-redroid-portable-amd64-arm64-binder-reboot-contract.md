# Android cloud 100% — bootstrap ReDroid ARM64/AMD64 com recuperação após reboot
STATUS: PARTIAL
AREA: android
DATE: 2026-11-13
RUN: none (OCI sem capacidade; nenhuma VPS externa com acesso root comprovado)
JOB: ARA 4a169c3298434a71b3f1457fb432a38f
COMMIT: branch feat/redroid-portable-amd64-arm64-20261113
SUPERSEDES: test-hub/findings/20261113-free-vps-vendor-availability-binder-readonly-gate.md

## BASELINE_PROVEN
Oracle Compute A1 e E2.1.Micro apresentaram OUT_OF_HOST_CAPACITY em 13/11/2026 15:10 UTC (ARA 5c14f2f90b4f1139459c697d6fd5ae81). O bootstrap só aceitou ARM64, e mesmo se uma VPS Linux AMD64 gratuita fosse obtida, a imagem ARM64 impediria o startup.

## CHANGE
- `infra/oci-android/redroid-firstboot.cloud-config.yml`: arquitetura ARM64/AMD64 selecionada por `uname -m` e manifesto Docker por SHA256 validado na API Docker Hub em 13/11/2026:
  ARM64 `3c7f9450188226bf8042c0159b9b38abe2106f1ceb0dfa45fae1cbc6409cd9bb`,
  AMD64 `e6f799d56b9a9a2bbc6224b5b7a6dc744c9b4d878ac856f27f0c4ec793ef55d3`.
- `write_files` grava `/etc/modules-load.d/anthares-redroid.conf` com `binder_linux` e `/etc/modprobe.d/anthares-redroid.conf` com as opções dos três dispositivos, para persistir após reboot.
- O script inicia novamente container existente que esteja parado; somente baixa imagem se container não existe. Preserva volume persistente, ADB ligado somente ao localhost e guardas fail-closed.
- `tools/oci_a1_capacity_watch.py` valida ambos os digests, plataforma selecionável, configuração de binder pós-reboot e recovery antes de enviar cloud-init à API OCI; `tests/test_oci_a1_capacity_watch.py` inclui regressões das proteções.

## TEST_VALIDITY
22 testes Python PASS / 0 FAIL / 0 ERROR; PyYAML validado, Bash `-n` OK, quatro seleções de plataforma simuladas em Bash isolado a partir do case real do cloud-init (aarch64, arm64, x86_64, amd64), módulos de reboot lidos e ordenação verificada, ARA `4a169c3298434a71b3f1457fb432a38f`. Testes não iniciaram Docker, não alteraram SO Windows, não contataram Neon nem Kwai.

## LIMITS
Ainda não foi obtida VM gratuita compatível nem ativado o monitor OCI no GitHub Actions. Persistência real de binder, execução privilegiada, instalação ReDroid, autenticação Kwai/MacroDroid e failover com leases Neon NÃO foram homologados. A imagem AMD64 é a mesma release ReDroid 12, com digest diferente, comprovado pela API Docker Hub. Não há despesa ou publicação nova.

## NEXT
Na primeira VM Ubuntu root com recursos suficientes e custo zero verificado, executar o read-only `tools/redroid_free_vps_preflight.py`, conferir binder e docker, iniciar cloud-init e comprovar ADB local, persistência após reboot e depois autenticação e postagem isolada em ambiente aprovado. Só promover à produção após confronto com lease/fencing Neon e garantia de nenhuma duplicata.
