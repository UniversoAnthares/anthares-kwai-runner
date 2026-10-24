# CORTES F1 — runtime isolado versionado, lease encerrado
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-24
RUN: GitHub anthares-clipper PR #194
JOB: chatgpt-cortes-drive-f1-runtime-20261024
COMMIT: UniversoAnthares/anthares-clipper@7296299623d81236024e3cadbef734b0fd2c901d
SUPERSEDES: none

## Objetivo
Versionar sem credenciais o runtime CORTES F1 instalado no Windows, sem mesclar o amplo PR #190 e sem alterar publicadores.

## Resultado
PR #194 foi mesclado via fluxo normal do GitHub. Quatro arquivos críticos tiveram conteúdo/hash de blob conferido contra o runtime SYSTEM ou feature auditada:
- tools/run_f1.py: 2c7debe60c42fbddce5cee3e01c89fdfbe61fc57
- tools/lock_recovery.py: 7f2414253240c8a0935319e933b4f41888f906ce
- cortes_drive_replica_guard.py: 8fa0934c60e2401d31cffcb6f0b9d89740dd7402
- cortes_cloud_drive_capacity.py: 48311ab7fa346168abd45f90add9b1101a72df2b
Incluídos tests/test_cortes_drive_replica_guard.py e docs/CORTES_F1_DRIVE_RUNTIME.md.
Agendamento Windows SYSTEM foi instalado e comprovado separadamente no finding 20261024-1306-cortes-drive-f1-scheduled-synthetic-recovery-partial.md.
PR #190 recebeu comentário de coordenação para não misturar migração cloud pendente com o sidecar ativo.
No GitLab main, cortes_google_drive_backup.py estava ausente no momento da comparação. Nenhum espelho cego, force-push ou substituição concorrente foi feito.

## Consequência
Versão do runtime agora é reconstruível a partir de main. O estado deste lease de versionamento é PROVEN e ENCERRADO. A aceitação operacional de backup de master real permanece PARTIAL até surgir mídia elegível na origem e passar por upload 2×, SHA e restauração. Não inferir backup de produção da tarefa idle ou do canário.
