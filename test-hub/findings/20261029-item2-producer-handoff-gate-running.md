# Item fixo 2 — preparação de handoff do produtor TikTok Neon GitHub → Forgejo
STATUS: RUNNING
AREA: tiktok/forgejo-producer-handoff
DATE: 2026-10-29 UTC
RUN: none
JOB: none
COMMIT: 95ccfe64312c571cd88b0d289f04cb8d4910eb95 (clipper baseline)
SUPERSEDES: none
LEASE: exclusivo para a alteração mínima em UniversoAnthares/anthares-clipper/.github/workflows/anthares-tiktok-owned-youtube.yml; liberar após prova de merge/readback.

BASELINE_PROVEN: produtor GitHub agendado a cada 5 minutos no workflow canônico, runner Windows; código Forgejo WordPress já tem preflight real #238 SUCCESS, mas admissão produtiva sem proof. Dez registros uncertain na tabela cortes_tiktok_publications são históricos de 2026-10-27; 12 entradas novas e distintas foram criadas em 2026-10-29 12:28 UTC, origem não atribuível apenas pelos campos do Neon. Nas execuções antigas Forgejo Clipper #1, #2, #3 o usuário comprovou estado cancelado.
FAILED_AVOIDED: ativação simultânea de GitHub e Forgejo, manipulação de Neon/estado uncertain, reenfileiramento experimental, tentativa de consulta administrativa Forgejo já recusada por segurança, publicações ou novas despesas.
SUCCESS_SIGNAL: adicionar guard explícito vars.CORTES_FORGEJO_PRODUCER_ENABLED != 'true' nos dois jobs GitHub (enqueue e relay). Gate ausente/false preserva o produtor GitHub; true interrompe novas admissões GitHub. Verificar alteração no SHA exato do GitHub e teste estático para os dois jobs. Isto é apenas PREPARAÇÃO; cutover só após prova de nenhum run GitHub ativo, ativação Forgejo autorizada, execução real produtiva e leitura independente da fila Neon.
FAILURE_SIGNAL: job GitHub sem guarda, alterações nas rotas de publicação, divergência de SHA, merge concorrente ou run Forgejo não comprovado.
TEST_VALIDITY: verificação contratual de source/YAML, sem efeitos na fila e sem publicação. Merge isolado não constitui migração completa.
PRESERVATION: não alterar schedules, tokens, mídia, runner, fila, contas ou publicadores.