# Handoff: TikTok caller must send central confirmation evidence when remote_id is absent
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-05
RUN: none
JOB: readonly-cross-agent-audit
COMMIT: 83e45c43c001766c8fc179e28d278c44a64d3b68
SUPERSEDES: none

## Objetivo
Verificar compatibilidade dos chamadores com a nova invariável fail-closed do controlador sem mutar tiktok-publish durante run ativo.

## Resultado
anthares-tiktok-owned-youtube.yml atualmente envia confirmed=true e remote_id, mas remote_id pode ser vazio mesmo quando a evidência UI confirmou publicação. O novo controlador exige remote_id OU confirmation_evidence. Portanto o chamador precisará incluir confirmation_evidence derivada da evidência já validada quando remote_id não existir.

## Evidência decisiva
Workflow privado contém bloqueio publication evidence missing quando evidence.confirmed é falso, mas o payload de /job/complete atualmente contém apenas executor, id, confirmed e remote_id.

## Consequência
CHAT responsável por tiktok-publish deve adaptar o payload depois do run ativo, preservando a validação existente. Não remover a guarda do controlador. Não mutado aqui por ownership/lease.
