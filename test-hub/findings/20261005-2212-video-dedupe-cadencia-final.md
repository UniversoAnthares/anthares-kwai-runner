# Endurecimento final de cortes e contenção TikTok
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/37379665325
JOB: 111998065487
COMMIT: c754f1e094f872e41cce311b7d21f171f81293fc, 076f3066e1a1c45b86684520cddc8e47807ca307, e57a237a3084412a5660234ace24513c4fc682fd, e95875b3e4c77e0cb7c2967c23e84b7ae325a870, 787ad9543797ace26e517e85c49206e80c88c7ea
SUPERSEDES: none

## Objetivo
Completar as redundâncias contra repetição de timeline e conter o padrão de publicação TikTok associado ao incidente de 0-3 views.

## Resultado
O plano TikTok agora carrega source_start/source_end até a fila central. O Durable Object recebeu dedupe por interseção temporal da mesma source_id, além de dedupe_key. O self-test do controlador ganhou caso de sobreposição de 1 segundo. A tentativa automática de deploy Cloudflare disparou no push e falhou imediatamente no GitHub Actions privado, portanto a nova barreira central ainda não pode ser classificada PROVEN em produção.

A geração local já havia sido endurecida para zero sobreposição. Como contenção do incidente TikTok, a automação foi reduzida de 100 para 3 publicações/dia e o espaçamento passou para 3-6 horas. As metas parciais agora derivam de DAILY_TARGET em vez dos valores fixos 33/66/100. Essa contenção reduz a variável de rajada enquanto se mede distribuição; não prova a causa do baixo alcance.

## Evidência decisiva
Run 37379665325, job 111998065487: workflow Anthares Cloudflare Deploy Once terminou failure segundos após iniciar. O código novo está no main, porém o deploy não foi confirmado. O pipeline e workflow agora persistem start/end e o controlador recusa Math.max(start,ps) < Math.min(end,pe).

## Consequência
Considerar PROVEN a regra de zero sobreposição no gerador já alterado; considerar PARTIAL a redundância central até um deploy Cloudflare confirmado. Não restaurar 100/dia/61-300s durante o diagnóstico de distribuição. Próximo teste TikTok deve usar poucos posts espaçados e comparar alcance com os posts manuais, sem reusar timeline. O executor público permanece a direção operacional; PC continua fora da produção.
