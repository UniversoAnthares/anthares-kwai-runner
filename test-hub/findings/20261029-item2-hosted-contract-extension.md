# Item 2 — extensão mínima do lease para CI Python hospedado
STATUS: RUNNING
AREA: tiktok/forgejo-producer-contract
DATE: 2026-10-29 UTC
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40906681336
JOB: 123563244201
COMMIT: 5dcb1571952510afb161ad63b602d8256364c111
SUPERSEDES: 20261029-item2-local-editorial-bridge-lease.md
LEASE: estender a alteração da PR #226 somente ao arquivo .github/workflows/cortes-tiktok-producer-contract.yml do mesmo repositório Clipper, preservando workflow produtivo, políticas e filas. Windows self-hosted test permanece QUEUED sem execução; os testes só usam Python stdlib/unittest, sem secrets/infra/WordPress/Neon. Usar runner github-hosted ubuntu-24.04 exclusivamente no CI do contrato para comprovar regressão sem dependência de PC. Ao final, remover reserva após merge e readback. Não realizar publicação, token handoff, alteração de Neon ou Forgejo admin.