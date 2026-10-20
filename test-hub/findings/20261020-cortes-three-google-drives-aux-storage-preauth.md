# CORTES — armazenamento auxiliar em três Google Drives
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-20
RUN: none
JOB: Anthares Remote 626ec5f2fc21664cff78c20ae1f36930
COMMIT: UniversoAnthares/anthares-clipper@0a3d5ae74bb512dd053f3cd61affcd57d1c79c27
SUPERSEDES: none

## Evidências
Pastas Google Drive criadas nas três contas prioritárias, IDs 1zqrNuPS1EX9U6i0lo7ydQKFMmehvLHoN, 1s69dmiuCg2BcI690kpF02k978HlQhn-B, 1Kpg40qcIspuPfilU0tLMNkiH5crbZudq. A conta lucasyahn@gmail.com permanece exclusivamente para redundância.

PR #93 em anthares-clipper incorporado. `cortes_google_drive_backup.py` suporta cópia auxiliar não bloqueante, arquivos locais imutáveis, distribuição por remotes, confirmação de SHA-256 remoto com streaming e ledger. Quatro testes locais passaram no Windows. Dry run retornou `not_configured`, `uploaded:0`, `verified:0`.

## Bloqueio real
Credenciais OAuth existentes no ChatGPT Google Drive NÃO equivalem a OAuth rclone no executor Windows. No Windows não havia `rclone` nem três remotes autenticados; portanto nenhum upload de vídeo real foi verificado. Não declarar operação de backup ativada nem limpar masters com base nesses passos. Antes do aceite, configurar remotes autorizados nas três contas, testar arquivo pequeno, validar readback SHA-256 e execução não assistida, sem interromper publicações.
