# CORTES — retomada segura de fanout de três redes a partir de fonte WordPress
STATUS: PARTIAL
AREA: cortes-cloud-fanout
DATE: 2026-11-10 UTC
OWNER: chatgpt-pinterest-clipper-daily-20261110
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2303

## Linha de base
- Workflow cloud .github/workflows/cortes-buffer-three-fanout-cloud.yml estava disabled_manually. Últimas sete execuções até 2026-11-01 registravam falha RuntimeError antes de emitir estado por destino. Run 41265680140 foi inspecionada.
- O script é só produtor Neon da fila Instagram, Pinterest e LinkedIn, idempotente por ID e conta. Não renderiza clipes e não publica nas redes.
- Cron legado a cada 10 minutos era excessivo e podia multiplicar chamadas GitHub/Neon sem gerar cortes novos.

## Alteração
- 3 disparos de distribuição por dia (07h23, 13h23, 19h23, MS), usando Ubuntu efêmero hospedado, sem PC.
- O disparo manual diagnose_only consulta a fonte e conta candidatos sem enqueues. Falhas em preflight apresentam estágio e apenas códigos seguros (sem dados privados).
- Testes offline cobrem diagnóstico sem mutação, três destinos com dedupe e isolamento de falhas de leitura.
- Nenhum workflow Windows foi reativado. A geração completa de novos masters ainda depende de persistência/ledger e de mídia externa homologados.

## Aceite pendente
- Fazer o teste diagnose_only real, comprovar identidade e estado da fonte, corrigir impedimentos e então habilitar execução efetiva sob quota.
- Confirmar novos enqueues por plataforma no Neon; entregar provas públicas por publicador independentemente.
- Registrar separadamente o cutover de cortes-daily/short-resume para fora do Windows. Estado do renderizador permanece BLOCKED.
